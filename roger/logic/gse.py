from abc import ABC, abstractmethod
from typing import List

import pandas as pd
import tempfile
from pandas import DataFrame, read_table
from numpy import log10, abs
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import ListVector
from rpy2 import robjects
from sqlalchemy.orm import Session

pandas2ri.activate()

from roger.persistence.schema import DGEmodel, GeneSetCategory, GeneSet, GSEmethod, DGEmethod, GSEtable
from roger.util import as_data_frame

DGE_MODEL_SUB_FOLDER = "dge_model"

base = importr("base")
utils = importr("utils")
biobase = importr("Biobase")
ribios_ngs = importr("ribiosNGS")
ribios_gsea = importr("ribiosGSEA")
ribios_utils = importr("ribiosUtils")


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
    def exec_gse(self, dge_model, gscs) -> pd.DataFrame:
        """Executes the GSE algorithm on the given data"""
        pass


class EdgeRCamera(GSEAlgorithm):
    @property
    def name(self) -> str:
        return "CAMERA"

    @property
    def description(self) -> str:
        return "CAMERA for edgeR"

    def exec_gse(self, dge_model, gscs) -> pd.DataFrame:
        gse_res = ribios_ngs.doGse(dge_model, gscs)
        enrich_tbl_file, enrich_tbl_file_path = tempfile.mkstemp()
        utils.write_table(ribios_ngs.fullEnrichTable(gse_res), enrich_tbl_file_path, sep="\t")
        return read_table(enrich_tbl_file_path)


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

    def exec_gse(self, dge_model, gscs) -> pd.DataFrame:
        eset_gene_symbols = getGeneSymbols(biobase.fData(dge_model))
        camera_result = esetCamera(dge_model, eset_gene_symbols,
                                  dge_model.Contrast.Design.design_matrix,
                                  dge_model.Contrast.contrast_matrix,
                                  gscs)
        enrich_tbl_file, enrich_tbl_file_path = tempfile.mkstemp()
        utils.write_table(camera_result, enrich_tbl_file_path, sep="\t")
        return read_table(enrich_tbl_file_path)


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
                dge_model: DGEmodel,
                algorithm: GSEAlgorithm,
                gene_set_category_filter: List[str] = None):
    dge_model_path = dge_model.FitObjFile
    dge_fit_obj = base.readRDS(dge_model_path)

    gene_sets = get_gmt_locations(session, gene_set_category_filter)
    gscs_list = {gene_set.Category: gene_set.FileWC for index, gene_set in gene_sets.iterrows()}
    gscs = ribios_gsea.readGmt(ListVector(gscs_list))

    contrast_columns = dge_model.Contrast.contrast_columns

    gse_method_id = session.query(GSEmethod.ID) \
        .filter(GSEmethod.DGEmethodID == DGEmethod.ID) \
        .filter(DGEmethod.ID == dge_model.Method.ID) \
        .filter(GSEmethod.Name == algorithm.name).scalar()

    enrich_tbl = algorithm.exec_gse(dge_fit_obj, gscs)

    gene_sets.Category = gene_sets.Category.str.lower()
    gene_sets.Name = gene_sets.Name.str.lower()
    enrich_tbl.Category = enrich_tbl.Category.str.lower()
    enrich_tbl.GeneSet = enrich_tbl.GeneSet.str.lower()
    merged_enrich_tbl = enrich_tbl.join(gene_sets.set_index(['Category', 'Name']), on=['Category', "GeneSet"]).join(
        contrast_columns.set_index("Name"), on="Contrast", lsuffix="_GENE_SET")

    gse_tbl = DataFrame({
        "ContrastColumnID": merged_enrich_tbl.ID,
        "GSEmethodID": gse_method_id,
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
    return mapped
