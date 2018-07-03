from enum import Enum
import pandas as pd

import roger.persistence.geneanno
from roger.logic.mart import get_annotation_service
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

    all_sym = ensembl_dataset.get_bulk_query({
        "attributes": [symbol_type, "ensembl_gene_id"],
        "filters": {
            "with_%s" % symbol_type: True
        }
    })

    # TODO FeatureIndex starts at 1, but should be fixed later on
    feature_anno = pd.DataFrame(data={"Name": gct_data.data_df.index,
                                      "FeatureIndex": range(1, gct_data.data_df.shape[0] + 1)},
                                index=gct_data.data_df.index)
    feature_anno = feature_anno.join(all_sym.set_index(symbol_type))

    # TODO We should not "drop" multiple genes that map to the same chip id ...
    feature_anno = feature_anno[~feature_anno.index.duplicated(keep='first')]
    feature_anno = feature_anno.set_index("ensembl_gene_id")

    # TODO include origin tax id and origin roger gene index
    query = session.query(GeneAnnotation.RogerGeneIndex, GeneAnnotation.EnsemblGeneID).filter_by(TaxID=tax_id)
    if tax_id != human_tax_id:
        query = session\
            .query(Ortholog.HumanRogerGeneIndex.label("RogerGeneIndex"), GeneAnnotation.EnsemblGeneID)\
            .filter(GeneAnnotation.RogerGeneIndex == Ortholog.RogerGeneIndex)\
            .filter(GeneAnnotation.TaxID == tax_id)
    roger_gene_indices = roger.util.as_data_frame(query)
    feature_anno = feature_anno.join(roger_gene_indices.set_index("EnsemblGeneID"))\
        .drop_duplicates("FeatureIndex").\
        sort_values('FeatureIndex').\
        reset_index().drop(columns="index")
    # TODO just return version of dataset
    return feature_anno, ensembl_dataset.display_name
