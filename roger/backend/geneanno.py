from roger.backend.schema import GeneAnnotation, Ortholog
from roger.exception import ROGERUsageError
from roger.util import as_data_frame

from biomart import BiomartServer
from pandas.compat import cStringIO
import pandas as pd
import re

human_dataset = "hsapiens_gene_ensembl"
human_tax_id = 9606


def query_biomart_by_ds_name(dataset_name, params):
    server = BiomartServer("http://www.ensembl.org/biomart")
    dataset = server.datasets[dataset_name]
    response = dataset.search(params=params)
    result = pd.read_csv(cStringIO(response.text), sep='\t', names=params['attributes'])
    return result


def query_biomart_by_ds(dataset, params):
    response = dataset.search(params=params)
    result = pd.read_csv(cStringIO(response.text), sep='\t', names=params['attributes'])
    return result


def list_species(session):
    return as_data_frame(session.query(GeneAnnotation.TaxID, GeneAnnotation.Version)
                         .group_by(GeneAnnotation.TaxID, GeneAnnotation.Version))


def remove_species(session, tax_id):
    # Check if dataset is already preset in the database
    species_table = list_species(session)
    if tax_id == human_tax_id:
        raise ROGERUsageError('Cannot delete gene annotation from human species')
    if species_table[species_table.TaxID == tax_id].empty:
        raise ROGERUsageError('Species does not exist in database: %s' % tax_id)

    session.query(GeneAnnotation).filter(GeneAnnotation.TaxID == tax_id).delete()
    session.commit()


def nan_to_none(val):
    import math
    if math.isnan(val):
        return None
    return val


# TODO Check if dataset exist in Ensembl BioMart ...
def add_species(session, dataset, tax_id):
    # Check if dataset is already preset in the database
    species_table = list_species(session)

    if species_table[species_table.TaxID == human_tax_id].empty and human_tax_id != tax_id:
        raise ROGERUsageError('No human species annotation data present - import human gene annotation first')
    if not species_table[species_table.TaxID == tax_id].empty:
        raise ROGERUsageError('Species already exists in database: %s' % dataset)

    homolog_attr = re.sub(r'(\w+)_gene_ensembl', r'\1_homolog_ensembl_gene', dataset)
    homolog_filter = re.sub(r'(\w+)_gene_ensembl', r'with_\1_homolog', dataset)

    # Insert Gene annotation

    server = BiomartServer("http://www.ensembl.org/biomart")
    version = "%s %s" % (dataset, re.search(r'[^(]+\(([^)]+)\)', server.datasets[dataset].display_name).group(1))

    gene_anno = query_biomart_by_ds_name(dataset, params={
        'attributes': [
            "ensembl_gene_id", "entrezgene", "gene_biotype", "external_gene_name"
        ]
    })
    genes = gene_anno.apply(lambda row: GeneAnnotation(Version=version,
                                                       TaxID=tax_id,
                                                       EnsemblGeneID=row.ensembl_gene_id,
                                                       EntrezGeneID=nan_to_none(row.entrezgene),
                                                       GeneType=row.gene_biotype,
                                                       GeneSymbol=row.external_gene_name,
                                                       IsObsolete=False), axis=1)
    session.bulk_save_objects(genes)

    # Insert orthologs
    huma_anno_query = as_data_frame(session.query(GeneAnnotation).filter(GeneAnnotation.TaxID == human_tax_id))

    if tax_id == human_tax_id:
        orthologs = huma_anno_query.apply(lambda row: Ortholog(RogerGeneIndex=row.RogerGeneIndex,
                                                               HumanRogerGeneIndex=row.RogerGeneIndex), axis=1)
        session.bulk_save_objects(orthologs)
        session.commit()
        return

    anno_query = as_data_frame(session.query(GeneAnnotation).filter(GeneAnnotation.TaxID == tax_id))
    ortho = query_biomart_by_ds_name(human_dataset, params={
        'attributes': [
            "ensembl_gene_id", homolog_attr
        ],
        'filters': {
            homolog_filter: True
        }
    })
    merged_ortho = ortho.join(huma_anno_query.set_index('EnsemblGeneID'), on='ensembl_gene_id')\
        .join(anno_query.set_index('EnsemblGeneID'), on=homolog_attr, lsuffix='Human', rsuffix='Other')

    orthologs = merged_ortho.apply(lambda row: Ortholog(RogerGeneIndex=row.RogerGeneIndexOther,
                                                        HumanRogerGeneIndex=row.RogerGeneIndexHuman), axis=1)
    session.bulk_save_objects(orthologs)
    session.commit()
