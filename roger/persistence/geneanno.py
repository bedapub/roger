import re
from pandas import DataFrame

from roger.persistence.schema import GeneAnnotation, Ortholog
from roger.logic.util.exception import ROGERUsageError
from roger.logic.util.data import as_data_frame, insert_data_frame, get_next_free_db_id
import roger.logic.mart.provider

human_dataset = "hsapiens_gene_ensembl"
human_tax_id = 9606


def init(db):
    db.create_all()
    add_species(db.session(), human_dataset, human_tax_id)


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


def add_species(session, dataset_name, tax_id):
    annotation_service = roger.logic.mart.provider.get_annotation_service()
    # Check if dataset is already preset in the database
    species_table = list_species(session)

    if species_table[species_table.TaxID == human_tax_id].empty and human_tax_id != tax_id:
        raise ROGERUsageError('No human species annotation data present - import human gene annotation first')
    if not species_table[species_table.TaxID == tax_id].empty:
        raise ROGERUsageError('Species already exists in database: %s' % dataset_name)

    homolog_attr = re.sub(r'(\w+)_gene_ensembl', r'\1_homolog_ensembl_gene', dataset_name)
    homolog_filter = re.sub(r'(\w+)_gene_ensembl', r'with_\1_homolog', dataset_name)

    # Insert Gene annotation
    dataset = annotation_service.get_dataset(dataset_name)
    # TODO fix this, should move into provider.py
    version = "%s %s" % (dataset_name, re.search(r'[^(]+\(([^)]+)\)', dataset.display_name).group(1))

    gene_anno = dataset.get_bulk_query(params={
        'attributes': [
            "ensembl_gene_id", "entrezgene", "gene_biotype", "external_gene_name"
        ]
    })

    next_id = get_next_free_db_id(session, GeneAnnotation.RogerGeneIndex)

    genes = DataFrame({'RogerGeneIndex': range(next_id, next_id + gene_anno.shape[0]),
                       'Version': version,
                       'TaxID': tax_id,
                       'EnsemblGeneID': gene_anno["ensembl_gene_id"],
                       'EntrezGeneID': gene_anno["entrezgene"],
                       'GeneType': gene_anno["gene_biotype"],
                       'GeneSymbol': gene_anno["external_gene_name"],
                       'IsObsolete': False})
    insert_data_frame(session, genes, GeneAnnotation.__table__)

    # Insert orthologs
    if tax_id == human_tax_id:
        orthologs = DataFrame({'RogerGeneIndex': genes["RogerGeneIndex"],
                               'HumanRogerGeneIndex': genes["RogerGeneIndex"]})
        insert_data_frame(session, orthologs, Ortholog.__table__)
        session.commit()
        return

    huma_anno_query = as_data_frame(session.query(GeneAnnotation).filter(GeneAnnotation.TaxID == human_tax_id))
    ortho = annotation_service.get_bulk_query(human_dataset, params={
        'attributes': [
            "ensembl_gene_id", homolog_attr
        ],
        'filters': {
            homolog_filter: True
        }
    })
    merged_ortho = ortho.join(huma_anno_query.set_index('EnsemblGeneID'), on='ensembl_gene_id') \
        .join(genes.set_index('EnsemblGeneID'), on=homolog_attr, lsuffix='Human', rsuffix='Other')

    orthologs = DataFrame({'RogerGeneIndex': merged_ortho["RogerGeneIndexOther"],
                           'HumanRogerGeneIndex': merged_ortho["RogerGeneIndexHuman"]})
    insert_data_frame(session, orthologs, Ortholog.__table__)
    session.commit()
