from functools import reduce
from gseapy.parser import gsea_gmt_parser
import pandas as pd
import sys
from sqlalchemy import func

from roger.persistence.schema import GSEmethod, GeneSetCategory, GeneSet, GeneSetGene
from roger.persistence.geneanno import GeneAnnotation
from roger.util import as_data_frame
from roger.exception import ROGERUsageError


def list_methods(session):
    return as_data_frame(session.query(GSEmethod.Name, GSEmethod.Description, GSEmethod.Version))


def add_method(session, name, description, version):
    method = GSEmethod(Name=name, Description=description, Version=version)
    session.add(method)
    session.commit()


def delete_method(session, name):
    # Check if GSE method is already preset in the database
    gse_methods = list_methods(session)
    if gse_methods[gse_methods.Name == name].empty:
        raise ROGERUsageError('GSE does not exist in database: %s' % name)

    session.query(GSEmethod).filter(GSEmethod.Name == name).delete()
    session.commit()


def list_gmt(session):
    return as_data_frame(session.query(GeneSetCategory.Name, func.count(GeneSet.ID).label("GeneSetCount"))
                         .filter(GeneSetCategory.ID == GeneSet.CategoryID)
                         .group_by(GeneSetCategory.Name))


# TODO: Support annotation of genes based on identifier types other than just gene symbols
def add_gmt(session, category_name, file, tax_id, description=None):
    gene_anno = as_data_frame(session.query(GeneAnnotation).filter(GeneAnnotation.TaxID == tax_id))
    # TODO Make min_size configurable?
    gmt = gsea_gmt_parser(file, min_size=1, max_size=sys.maxsize)
    category = GeneSetCategory(Name=category_name)
    session.add(category)
    session.flush()
    gene_sets = [GeneSet(Category=category, Name=gene_set_name, TaxID=tax_id, Description=description,
                         GeneCount=len(genes), IsPrivate=False)
                 for gene_set_name, genes in gmt.items()]
    session.add_all(gene_sets)
    session.flush()
    gene_set_dict = {gene_set.Name: gene_set for gene_set in gene_sets}
    genes_table_list = [pd.DataFrame({'GeneSetID': gene_set_dict[gene_set_name].ID, 'GeneSymbol': genes})
                        for gene_set_name, genes in gmt.items()]
    genes_table = reduce(lambda a, b: a.append(b), genes_table_list, pd.DataFrame())
    annotated_genes = genes_table.join(gene_anno.set_index('GeneSymbol'), on='GeneSymbol')
    # Filter out non-matching genes
    matched_genes = annotated_genes[annotated_genes.RogerGeneIndex.notna()]\
        .drop_duplicates(subset=['RogerGeneIndex', 'GeneSetID'], keep=False)

    # Bulk insert all gene set genes
    gene_set_genes = matched_genes.apply(lambda row: GeneSetGene(RogerGeneIndex=row.RogerGeneIndex,
                                                                 GeneSetID=row.GeneSetID), axis=1)
    session.bulk_save_objects(gene_set_genes)
    session.commit()

    # Report number of gene symbols that could not be matched with gene annotation
    p_unknown_gene_symbols = (annotated_genes.shape[0] - matched_genes.shape[0])/float(annotated_genes.shape[0])
    return p_unknown_gene_symbols


# TODO: Does not delete everything yet ...
def delete_gmt(session, category_name):
    # Check if gene set category is preset in the database
    gmt_list = list_gmt(session)
    if gmt_list[gmt_list.Name == category_name].empty:
        raise ROGERUsageError('GMT does not exist in database: %s' % category_name)

    session.query(GeneSetCategory).filter(GeneSetCategory.Name == category_name).delete()
    session.commit()
