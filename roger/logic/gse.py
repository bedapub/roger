import os
from abc import ABC, abstractmethod
from typing import List

import tempfile

from pandas import DataFrame, read_table
from numpy import log10, abs
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import ListVector
from rpy2 import robjects
from sqlalchemy import func
from sqlalchemy.orm import Session

from roger.logic.util.common import silent_remove
from roger.logic.util.exception import ROGERUsageError
from roger.persistence.schema import DGEmodel, GeneSetCategory, GeneSet, GSEmethod, DGEmethod, GSEresult, GSEtable, \
    Design, Contrast, DataSet
from roger.logic.util.data import as_data_frame, write_df, insert_data_frame

pandas2ri.activate()

GSE_RESULT_SUB_FOLDER = "gse_result"

limma = importr("limma")
base = importr("base")
utils = importr("utils")
biobase = importr("Biobase")
ribios_ngs = importr("ribiosNGS")
ribios_gsea = importr("ribiosGSEA")
ribios_utils = importr("ribiosUtils")


class GSEAlgorithmResult(object):
    """Result class that hold all relevant information produced by a DGE algorithm"""

    def __init__(self, raw_gse_table, method_desc):
        self.raw_gse_table = raw_gse_table
        self.method_desc = method_desc


class GSEAlgorithm(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of this GSE method"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Returns the description for this GSE method"""
        pass

    @abstractmethod
    def exec_gse(self, dge_model: DGEmodel, gscs) -> GSEAlgorithmResult:
        """Executes the GSE algorithm on the given data"""
        pass


class EdgeRCamera(GSEAlgorithm):
    @property
    def name(self) -> str:
        return "CAMERA"

    @property
    def description(self) -> str:
        return "CAMERA for edgeR"

    def exec_gse(self, dge_model: DGEmodel, gscs) -> GSEAlgorithmResult:
        dge_model_path = dge_model.FitObjFile
        dge_fit_obj = base.readRDS(dge_model_path)

        gse_res = ribios_ngs.doGse(dge_fit_obj, gscs)
        enrich_tbl_file, enrich_tbl_file_path = tempfile.mkstemp()
        utils.write_table(ribios_ngs.fullEnrichTable(gse_res), enrich_tbl_file_path, sep="\t")
        method_desc = "R ribiosGSEA version: %s" % ribios_gsea.__version__
        return GSEAlgorithmResult(read_table(enrich_tbl_file_path), method_desc)


getGeneSymbols = robjects.r('''
    function(featureTbl) {
        genes <- NULL
        if("GeneSymbol" %in% colnames(featureTbl)) {
            genes <- featureTbl[,"GeneSymbol"]
        } else if ("HumanGeneSymbol" %in% colnames(featureTbl)) {
            genes <- featureTbl[, "HumanGeneSymbol"]
        }
        if(is.null(genes)) return(NULL)
        if(mean(!is.na(genes))>=0.25) { ## when more than 25% probes are annotated 
            return(as.character(genes))
        } else {
            return(NULL)
        }
    }
''')

esetCamera = robjects.r('''
    function(eset, geneSymbols, design, contrasts, gscs) {
        categories <- gsCategory(gscs)
        cameraTables <- tapply(gscs, categories, function(gsc) {
                            tt <- gscCamera(exprs(eset), geneSymbols,
                                 gsc=gsc, design=design, contrasts=contrasts)
                            })
        cameraTable <- do.call(rbind, cameraTables)
        cameraTable$Category <- rep(names(cameraTables), sapply(cameraTables, nrow))
        cameraTable <- putColsFirst(cameraTable, "Category")
        rownames(cameraTable) <- NULL
        return(cameraTable)
    }
''')


class LimmaCamera(GSEAlgorithm):
    @property
    def name(self) -> str:
        return "CAMERA"

    @property
    def description(self) -> str:
        return "CAMERA for limma"

    def exec_gse(self, dge_model, gscs) -> GSEAlgorithmResult:
        dge_model_path = dge_model.InputObjFile
        dge_input_obj = base.readRDS(dge_model_path)

        eset_gene_symbols = getGeneSymbols(biobase.fData(dge_input_obj))
        camera_result = esetCamera(dge_input_obj, eset_gene_symbols,
                                   dge_model.Contrast.Design.design_matrix,
                                   dge_model.Contrast.contrast_matrix,
                                   gscs)
        enrich_tbl_file, enrich_tbl_file_path = tempfile.mkstemp()
        utils.write_table(camera_result, enrich_tbl_file_path, sep="\t")
        method_desc = "R ribiosGSEA version: %s" % ribios_gsea.__version__
        return GSEAlgorithmResult(read_table(enrich_tbl_file_path), method_desc)


def get_gmt_locations(session: Session, gene_set_category_filter: List[str] = None):
    query = session.query(GeneSetCategory.Name.label("Category"),
                          GeneSetCategory.FileWC,
                          GeneSet.ID,
                          GeneSet.Name) \
        .filter(GeneSetCategory.ID == GeneSet.CategoryID)

    if gene_set_category_filter:
        query = query.filter(GeneSetCategory.Name.in_(gene_set_category_filter))

    return as_data_frame(query)


def perform_gse(session: Session,
                roger_wd_dir: str,
                dge_model: DGEmodel,
                algorithm: GSEAlgorithm,
                gene_set_category_filter: List[str] = None):
    existing_results = get_gse_result(session,
                                      dge_model.Contrast.Name,
                                      dge_model.Contrast.Design.Name,
                                      dge_model.Contrast.Design.DataSet.Name,
                                      dge_model.Method.Name,
                                      algorithm.name)
    if existing_results:
        raise ROGERUsageError("Result for %s:%s:%s:%s:%s already exists" % (dge_model.Contrast.Name,
                                                                            dge_model.Contrast.Design.Name,
                                                                            dge_model.Contrast.Design.DataSet.Name,
                                                                            dge_model.Method.Name,
                                                                            algorithm.name))

    gene_sets = get_gmt_locations(session, gene_set_category_filter)
    gscs_list = {gene_set.Category: gene_set.FileWC for index, gene_set in gene_sets.iterrows()}
    gscs = ribios_gsea.readGmt(ListVector(gscs_list))

    contrast_columns = dge_model.Contrast.contrast_columns

    gse_method_id = session.query(GSEmethod.ID) \
        .filter(GSEmethod.DGEmethodID == DGEmethod.ID) \
        .filter(DGEmethod.ID == dge_model.Method.ID) \
        .filter(GSEmethod.Name == algorithm.name).scalar()

    gse_algo_result = algorithm.exec_gse(dge_model, gscs)
    enrich_tbl = gse_algo_result.raw_gse_table

    gene_sets.Category = gene_sets.Category.str.lower()
    gene_sets.Name = gene_sets.Name.str.lower()
    enrich_tbl.Category = enrich_tbl.Category.str.lower()
    enrich_tbl.GeneSet = enrich_tbl.GeneSet.str.lower()
    merged_enrich_tbl = enrich_tbl.join(gene_sets.set_index(['Category', 'Name']), on=['Category', "GeneSet"]).join(
        contrast_columns.set_index("Name"), on="Contrast", lsuffix="_GENE_SET")

    gse_method_sub_dir = "%d_%s" % (dge_model.Contrast.ID, algorithm.name)
    gse_models_path = os.path.join(roger_wd_dir, GSE_RESULT_SUB_FOLDER)
    gse_model_path = os.path.join(gse_models_path, gse_method_sub_dir)
    if not os.path.exists(gse_model_path):
        os.makedirs(gse_model_path)

    gse_result_file = os.path.join(gse_model_path, "gse_table.txt")
    write_df(enrich_tbl, gse_result_file)

    gse_result = GSEresult(ContrastID=dge_model.ContrastID,
                           DGEmethodID=dge_model.DGEmethodID,
                           GSEmethodID=gse_method_id,
                           OutputFile=gse_result_file,
                           MethodDescription=gse_algo_result.method_desc)
    session.add(gse_result)
    session.flush()

    gse_tbl = DataFrame({
        "GSEresultID": gse_result.ID,
        "ContrastColumnID": merged_enrich_tbl.ID,
        "GeneSetID": merged_enrich_tbl.ID_GENE_SET,
        "Correlation": merged_enrich_tbl.Correlation,
        "Direction": merged_enrich_tbl.Direction.map({"Up": 1, "Down": -1}),
        "PValue": merged_enrich_tbl.PValue,
        "FDR": merged_enrich_tbl.FDR,
        "EnrichmentScore": merged_enrich_tbl.Direction.map({"Up": 1, "Down": -1}) * abs(
            log10(merged_enrich_tbl.PValue)),
        "EffGeneCount": merged_enrich_tbl.NGenes
    })
    unmapped = gse_tbl[gse_tbl.GeneSetID.isnull()]
    mapped = gse_tbl[~gse_tbl.GeneSetID.isnull()]
    if unmapped.shape[0] > 0:
        print("Warning: unable to map %d of %d entries to gene sets " % (unmapped.shape[0], merged_enrich_tbl.shape[0]))

    mapped_duplications = mapped.drop_duplicates(subset=['ContrastColumnID', 'GeneSetID'])

    if mapped_duplications.shape[0] < mapped.shape[0]:
        print("Warning: %d of %d entries of mapped result entries are duplicated"
              % (mapped.shape[0] - mapped_duplications.shape[0], mapped.shape[0]))

    insert_data_frame(session, mapped_duplications, GSEtable.__table__)
    session.commit()


def get_gse_result(session, contrast, design, dataset, dge_method, gse_method) -> GSEresult:
    return session.query(GSEresult) \
        .filter(Contrast.DesignID == Design.ID) \
        .filter(Design.DataSetID == DataSet.ID) \
        .filter(DGEmodel.ContrastID == Contrast.ID) \
        .filter(DGEmodel.DGEmethodID == DGEmethod.ID) \
        .filter(GSEresult.ContrastID == Contrast.ID) \
        .filter(GSEresult.DGEmethodID == DGEmethod.ID) \
        .filter(GSEresult.GSEmethodID == GSEmethod.ID) \
        .filter(Contrast.Name == contrast) \
        .filter(Design.Name == design) \
        .filter(DataSet.Name == dataset) \
        .filter(DGEmethod.Name == dge_method) \
        .filter(GSEmethod.Name == gse_method).one_or_none()


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
        .filter(GSEresult.ContrastID == Contrast.ID) \
        .filter(GSEresult.DGEmethodID == DGEmethod.ID) \
        .filter(GSEresult.GSEmethodID == GSEmethod.ID) \
        .filter(GSEtable.GSEresultID == GSEresult.ID).group_by(GSEtable.GSEresultID)
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


def get_gse_table(session, contrast, design, dataset, dge_method, gse_method) -> DataFrame:
    gse_result = get_gse_result(session, contrast, design, dataset, dge_method, gse_method)

    if not gse_result:
        raise ROGERUsageError("GSE results for %s:%s:%s:%s:%s do not exist"
                              % (contrast, design, dataset, dge_method, gse_method))
    return gse_result.result_table


def remove_gse_table(session, contrast, design, dataset, dge_method, gse_method):
    gse_result = get_gse_result(session, contrast, design, dataset, dge_method, gse_method)
    silent_remove(gse_result.OutputFile)
    session.delete(gse_result)
    session.commit()
