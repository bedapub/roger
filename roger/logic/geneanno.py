from sqlalchemy.sql.expression import literal
from enum import Enum
import pandas as pd

import roger.persistence.geneanno
from roger.logic.mart.provider import get_annotation_service
from roger.exception import ROGERUsageError
from roger.persistence.geneanno import GeneAnnotation, Ortholog, human_tax_id
import roger.util


class CommonGeneIdentifier(Enum):
    ENSEMBL_GENE_ID = "ensembl_gene_id"
    ENTREZ_GENE_ID = "entrezgene"
    GENE_SYMBOL = "external_gene_name"


def get_dataset_of(session, tax_id):
    annotation_service = get_annotation_service()

    species_list = roger.persistence.geneanno.list_species(session)
    if species_list[species_list.TaxID == tax_id].empty:
        raise ROGERUsageError('Unknown taxon id: %s' % tax_id)

    dataset_name = species_list.loc[species_list["TaxID"] == tax_id, "Version"].values[0].split(' ')[0]

    return annotation_service.get_dataset(dataset_name)


def annotate(session, gct_data, tax_id, symbol_type):
    ensembl_dataset = get_dataset_of(session, tax_id)

    attributes = ensembl_dataset.attributes

    params = {
        "attributes": [symbol_type, "ensembl_gene_id"],
    }

    filter_attr = "with_%s" % symbol_type
    if filter_attr in attributes["name"]:
        params["filters"] = {filter_attr: True}

    all_sym = ensembl_dataset.get_bulk_query(params).dropna()

    feature_anno = pd.DataFrame(data={"Name": gct_data.index,
                                      "FeatureIndex": range(0, gct_data.shape[0])},
                                index=gct_data.index)

    # Pandas tries to convert columns to floats when possible,
    # but sometimes the expression files contais errors / mixed types and leave columns unconverted
    # In order to make joining possible for any edge case (look at rnaseq-example-readCounts.gct),
    # we have "normalize" the types, i.e. make them all 'str'
    feature_anno.Name = feature_anno.Name.apply(lambda x: "%d" % x if type(x) != str else x)
    all_sym[symbol_type] = all_sym[symbol_type].apply(lambda x: "%d" % x if type(x) != str else x)

    feature_anno = feature_anno.join(all_sym.set_index(symbol_type))

    # TODO Find a better heuristic to drop multiple Ensembl ID association
    feature_anno = feature_anno[~feature_anno.index.duplicated(keep='first')]
    feature_anno = feature_anno.set_index("ensembl_gene_id")

    # TODO include origin tax id and origin roger gene index
    query = session.query(GeneAnnotation.RogerGeneIndex,
                          GeneAnnotation.RogerGeneIndex.label("OriRogerGeneIndex"),
                          literal(human_tax_id).label("OriTaxID"),
                          GeneAnnotation.EnsemblGeneID) \
        .filter_by(TaxID=tax_id)
    if tax_id != human_tax_id:
        query = session \
            .query(Ortholog.HumanRogerGeneIndex.label("RogerGeneIndex"),
                   Ortholog.RogerGeneIndex.label("OriRogerGeneIndex"),
                   literal(tax_id).label("OriTaxID"),
                   GeneAnnotation.EnsemblGeneID) \
            .filter(GeneAnnotation.RogerGeneIndex == Ortholog.RogerGeneIndex) \
            .filter(GeneAnnotation.TaxID == tax_id)
    roger_gene_indices = roger.util.as_data_frame(query)
    # TODO Find a better heuristic to drop multiple Ensembl ID association
    feature_anno = feature_anno.join(roger_gene_indices.set_index("EnsemblGeneID")) \
        .drop_duplicates("FeatureIndex"). \
        sort_values('FeatureIndex'). \
        reset_index().drop(columns="index")
    return feature_anno, ensembl_dataset.display_name
