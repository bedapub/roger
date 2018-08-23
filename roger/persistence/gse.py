import shutil

from gseapy.parser import gsea_gmt_parser
import pandas as pd
import sys
import os.path

from sqlalchemy import func
from sqlalchemy.orm import Session

from roger.persistence.schema import GSEmethod, GeneSetCategory, GeneSet, GeneSetGene, DGEmethod, GSEtable, Contrast, \
    Design, DataSet, DGEmodel, ContrastColumn
from roger.persistence.geneanno import GeneAnnotation
from roger.util import as_data_frame, insert_data_frame
from roger.exception import ROGERUsageError

GENE_SET_SUB_FOLDER = "gene_sets"


def list_methods(session):
    return as_data_frame(session.query(GSEmethod.Name,
                                       GSEmethod.Description,
                                       DGEmethod.Name.label("Reference DGE Method"))
                         .filter(GSEmethod.DGEmethodID == DGEmethod.ID))


def add_method(session, method: DGEmethod, name: str, description: str):
    method = GSEmethod(DGEMethod=method, Name=name, Description=description)
    session.add(method)
    session.commit()
    return method


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
def add_gmt(session, roger_wd_dir, category_name, file, tax_id, description=None):
    gene_anno = as_data_frame(session.query(GeneAnnotation).filter(GeneAnnotation.TaxID == tax_id))
    # TODO Make min_size configurable?
    gmt = gsea_gmt_parser(file, min_size=1, max_size=sys.maxsize)

    gene_sets_path = os.path.join(roger_wd_dir, GENE_SET_SUB_FOLDER)
    file_copy_path = os.path.join(gene_sets_path, os.path.basename(file))

    category = GeneSetCategory(Name=category_name, FileWC=file_copy_path, FileSrc=os.path.abspath(file))
    session.add(category)

    if not os.path.exists(gene_sets_path):
        os.makedirs(gene_sets_path)
    shutil.copy(file, file_copy_path)

    session.flush()

    gene_sets = [GeneSet(Category=category,
                         Name=gene_set_name,
                         TaxID=tax_id,
                         Description=description,
                         GeneCount=len(genes),
                         IsPrivate=False)
                 for gene_set_name, genes in gmt.items()]
    session.add_all(gene_sets)
    session.flush()
    gene_set_dict = {gene_set.Name: gene_set for gene_set in gene_sets}

    gene_set_data = {'GeneSetID': [], 'GeneSymbol': []}
    for gene_set_name, genes in gmt.items():
        gene_set_data['GeneSetID'] += [gene_set_dict[gene_set_name].ID] * len(genes)
        gene_set_data['GeneSymbol'] += genes

    genes_table = pd.DataFrame.from_dict(gene_set_data)
    annotated_genes = genes_table.join(gene_anno.set_index('GeneSymbol'), on='GeneSymbol')
    # Filter out non-matching genes
    matched_genes = annotated_genes[annotated_genes.RogerGeneIndex.notna()] \
        .drop_duplicates(subset=['RogerGeneIndex', 'GeneSetID'], keep=False)

    # Bulk insert all gene set genes
    insert_data_frame(session, matched_genes, GeneSetGene.__table__, chunk_size=100000)
    session.commit()

    # Report number of gene symbols that could not be matched with gene annotation
    p_unknown_gene_symbols = (annotated_genes.shape[0] - matched_genes.shape[0]) / float(annotated_genes.shape[0])
    return p_unknown_gene_symbols


# TODO: Does not delete everything yet ...
def delete_gmt(session, category_name):
    # Check if gene set category is preset in the database
    gmt_list = list_gmt(session)
    if gmt_list[gmt_list.Name == category_name].empty:
        raise ROGERUsageError('GMT does not exist in database: %s' % category_name)

    session.query(GeneSetCategory).filter(GeneSetCategory.Name == category_name).delete()
    session.commit()


# -----------------
# GSE & execution
# -----------------


def query_gse_table(session, contrast, design, dataset, dge_method, gse_method):
    return session.query(GSEtable) \
        .filter(Contrast.DesignID == Design.ID) \
        .filter(Design.DataSetID == DataSet.ID) \
        .filter(DGEmodel.ContrastID == Contrast.ID) \
        .filter(DGEmodel.DGEmethodID == DGEmethod.ID) \
        .filter(ContrastColumn.ContrastID == Contrast.ID) \
        .filter(ContrastColumn.ID == GSEtable.ContrastColumnID) \
        .filter(GSEtable.GSEmethodID == GSEmethod.ID) \
        .filter(Contrast.Name == contrast) \
        .filter(Design.Name == design) \
        .filter(DataSet.Name == dataset) \
        .filter(DGEmethod.Name == dge_method) \
        .filter(GSEmethod.Name == gse_method)


def list_gse_tables(session, contrast, design, dataset, dge_method, gse_method):
    q = session.query(DataSet.Name.label("Data Set"),
                      Design.Name.label("Design"),
                      Contrast.Name.label("Contrast"),
                      DGEmethod.Name.label("DGE Method"),
                      GSEmethod.Name.label("GSE Method"),
                      func.count(GSEtable.GeneSetID).label("Entry Count")) \
        .filter(Contrast.DesignID == Design.ID) \
        .filter(Design.DataSetID == DataSet.ID) \
        .filter(DGEmodel.ContrastID == Contrast.ID) \
        .filter(DGEmodel.DGEmethodID == DGEmethod.ID) \
        .filter(ContrastColumn.ContrastID == Contrast.ID) \
        .filter(ContrastColumn.ID == GSEtable.ContrastColumnID) \
        .filter(GSEtable.GSEmethodID == GSEmethod.ID).group_by(GSEtable.GSEmethodID)
    if contrast is not None:
        q = q.filter(Contrast.Name == contrast)
    if design is not None:
        q = q.filter(Design.Name == design)
    if dataset is not None:
        q = q.filter(DataSet.Name == dataset)
    if dge_method is not None:
        q = q.filter(DGEmethod.Name == dge_method)
    if gse_method is not None:
        q = q.filter(GSEmethod.Name == gse_method)
    return as_data_frame(q)


def get_gse_table(session, contrast, design, dataset, dge_method, gse_method) -> pd.DataFrame:
    q = query_gse_table(session, contrast, design, dataset, dge_method, gse_method)
    gse_table = as_data_frame(q)

    if gse_table.empty:
        raise ROGERUsageError("GSE results for %s:%s:%s:%s:%s do not exist"
                              % (contrast, design, dataset, dge_method, gse_method))
    return gse_table


def create_gse_result(session: Session,
                      gse_table: pd.DataFrame):
    insert_data_frame(session, gse_table, GSEtable.__table__)
    session.commit()


def remove_gse_table(session, contrast, design, dataset, dge_method, gse_method):
    gse_entries = query_gse_table(session, contrast, design, dataset, dge_method, gse_method).all()
    for gse_entry in gse_entries:
        session.delete(gse_entry)
    session.commit()
