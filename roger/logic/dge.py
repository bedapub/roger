import tempfile
from typing import Type, List
from abc import ABC, abstractmethod

from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from rpy2 import robjects
import pandas as pd
import os.path

from roger.exception import ROGERUsageError
from roger.logic.geneanno import annotate
from roger.logic.gse import GSEAlgorithm, EdgeRCamera, LimmaCamera
from roger.persistence.dge import ROGER_SAMPLE_NAME, DataSetProperties, get_contrast, query_dge_models, add_method
from roger.persistence.gse import add_method as add_gse_method
from roger.persistence.geneanno import list_species
from roger.persistence.schema import DGEmethod, DGEtable, DGEmodel, \
    DataSet, FeatureSubset, Design
from roger.util import parse_gct, insert_data_frame, read_df, all_subclasses
from roger.logic.util.common import get_or_guess_name

DGE_MODEL_SUB_FOLDER = "dge_model"

pandas2ri.activate()

base = importr("base")
biobase = importr("Biobase")
ribios_io = importr("ribiosIO")
ribios_expression = importr("ribiosExpression")
ribios_ngs = importr("ribiosNGS")
utils = importr("utils")
methods = importr("methods")
limma = importr("limma")
ribios_roger = importr("ribiosROGER")


def annotate_ds_pheno_data(gct_data, pheno_data=pd.DataFrame()):
    if pheno_data.shape[0] > 0:
        if pheno_data.shape[0] != len(gct_data.columns):
            raise ROGERUsageError("Number of rows in pheno data and number of samples don't match: %d vs %d"
                                  % (pheno_data.shape[0], len(gct_data.columns)))

    if ROGER_SAMPLE_NAME not in pheno_data:
        pheno_data.insert(0, ROGER_SAMPLE_NAME, list(gct_data))
    if ROGER_SAMPLE_NAME in pheno_data and set(pheno_data[ROGER_SAMPLE_NAME]) != set(gct_data):
        raise ROGERUsageError("Sample names given by column '%s' don't match the sample names in expression data"
                              % ROGER_SAMPLE_NAME)

    return pheno_data


class DGEResult(ABC):
    """Result class that hold all relevant information produced by a DGE algorithm"""

    def __init__(self, input_obj, fit_obj, dge_table, used_feature_list, method_description):
        self.input_obj = input_obj
        self.fit_obj = fit_obj
        self.dge_table = dge_table
        self.used_feature_list = used_feature_list
        self.method_description = method_description


class DGEAlgorithm(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of this DGE method"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Returns the description for this DGE method"""
        pass

    @property
    @abstractmethod
    def gse_methods(self) -> List[Type[GSEAlgorithm]]:
        """Returns the available GSE methods for this particular DGE method"""
        pass

    @abstractmethod
    def exec_dge(self,
                 exprs_file: str,
                 feature_anno: pd.DataFrame,
                 design: Design,
                 contrast_matrix: pd.DataFrame,
                 **kwargs) -> DGEResult:
        """Executes the DGE algorithm on the given data"""
        pass


class LimmaDGE(DGEAlgorithm):
    @property
    def name(self) -> str:
        return "limma"

    @property
    def description(self) -> str:
        return "limma"

    @property
    def gse_methods(self) -> List[Type[GSEAlgorithm]]:
        return [LimmaCamera]

    def exec_dge(self,
                 exprs_file: str,
                 feature_anno: pd.DataFrame,
                 design: Design,
                 contrast_matrix: pd.DataFrame,
                 use_weighted: bool = False) -> DGEResult:

        fdf_file, fdf_file_path = tempfile.mkstemp()
        feature_anno.to_csv(fdf_file_path, sep="\t")

        design_data = design.design_matrix
        exprs_data = ribios_io.read_exprs_matrix(exprs_file)

        eset = methods.new("ExpressionSet", exprs=exprs_data)

        eset = biobase.__dict__["fData<-"](eset, utils.read_table(fdf_file_path, header=True, row_names=1, sep="\t"))

        weights = robjects.vectors.IntVector([1] * base.ncol(exprs_data)[0])
        if use_weighted:
            weights = limma.arrayWeights(eset, design=design_data)

        eset_fit = limma.lmFit(object=eset, design=design_data, weights=weights)
        eset_fit = limma.contrasts_fit(eset_fit, contrast_matrix)
        eset_fit = limma.eBayes(eset_fit)

        dge_tbl = pandas2ri.ri2py(ribios_roger.limmaDgeTable(eset_fit))

        used_names = robjects.conversion.ri2py(base.rownames(eset_fit.rx2("genes")))

        used_features = feature_anno['FeatureIndex'].isin(used_names)

        method_desc = "R limma version: %s" % limma.__version__

        return DGEResult(eset, eset_fit, dge_tbl, used_features, method_desc)


class EdgeRDGE(DGEAlgorithm):
    @property
    def name(self) -> str:
        return "edgeR"

    @property
    def description(self) -> str:
        return "edgeR"

    @property
    def gse_methods(self) -> List[Type[GSEAlgorithm]]:
        return [EdgeRCamera]

    def exec_dge(self,
                 exprs_file: str,
                 feature_anno: pd.DataFrame,
                 design: Design,
                 contrast_matrix: pd.DataFrame,
                 **kwargs) -> DGEResult:

        design_file, design_file_path = tempfile.mkstemp()
        contrast_file, contrast_file_path = tempfile.mkstemp()
        fdf_file, fdf_file_path = tempfile.mkstemp()

        design_matrix = design.design_matrix

        design_matrix.to_csv(design_file_path, sep="\t")
        contrast_matrix.to_csv(contrast_file_path, sep="\t")
        feature_anno.to_csv(fdf_file_path, sep="\t")

        exprs_data = ribios_io.read_exprs_matrix(exprs_file)

        descon = ribios_expression.parseDesignContrast(designFile=design_file_path,
                                                       contrastFile=contrast_file_path,
                                                       sampleGroups=base.paste(base.make_names(design.SampleGroups),
                                                                               collapse=","),
                                                       groupLevels=base.paste(base.make_names(design.SampleGroupLevels),
                                                                              collapse=","),
                                                       dispLevels=robjects.r("NULL"),
                                                       contrasts=robjects.r("NULL"))
        # expSampleNames=base.colnames(exprs_data))

        edger_input = ribios_ngs.EdgeObject(exprs_data, descon)

        slot = edger_input.slots["dgeList"]
        slot.rx2["genes"] = ribios_io.readTable(fdf_file_path)
        slot.rx2["annotation"] = "Name"
        edger_input.slots["dgeList"] = slot

        edger_result = ribios_ngs.dgeWithEdgeR(edger_input)

        dge_file, dge_file_path = tempfile.mkstemp()
        utils.write_table(ribios_ngs.dgeTable(edger_result), dge_file_path, sep="\t")
        dge_tbl = pd.read_table(dge_file_path)
        dge_tbl = dge_tbl.rename(index=str, columns={"logCPM": "AveExpr",
                                                     "LR": "t"})

        used_names = robjects.conversion.ri2py(biobase.featureNames(edger_result))
        used_features = feature_anno['Name'].isin(used_names)

        method_desc = "R ribiosNGS version: %s" % ribios_ngs.__version__

        return DGEResult(edger_input, edger_result, dge_tbl, used_features, method_desc)


def init_methods(session):
    for algorithm_class in all_subclasses(DGEAlgorithm):
        algorithm = algorithm_class()
        dge_method = add_method(session, algorithm.name, algorithm.description)
        for gse_algorithm_class in algorithm.gse_methods:
            gse_algorithm = gse_algorithm_class()
            add_gse_method(session, dge_method, gse_algorithm.name, gse_algorithm.description)


# ---------------
# Datasets
# ---------------

def create_ds(session,
              ds_type: Type[DataSet],
              exprs_file,
              tax_id,
              symbol_type,
              pheno_file=None,
              name=None,
              normalization_method=None,
              description=None,
              xref=None):
    name = get_or_guess_name(name, exprs_file)

    # Input checking
    species_list = list_species(session)
    if species_list[species_list.TaxID == tax_id].empty:
        raise ROGERUsageError('Unknown taxon id: %s' % tax_id)

    if session.query(DataSet).filter(DataSet.Name == name).one_or_none() is not None:
        raise ROGERUsageError("Data set with name '%s' already exists" % name)

    exprs_data = parse_gct(file_path=exprs_file)

    (annotation_data, annotation_version) = annotate(session, exprs_data, tax_id, symbol_type)

    pheno_data = pd.DataFrame()
    if pheno_file is not None:
        pheno_data = read_df(pheno_file)

    annotated_pheno_data = annotate_ds_pheno_data(exprs_data, pheno_data)

    return DataSetProperties(ds_type,
                             tax_id,
                             exprs_file,
                             pheno_file,
                             exprs_data,
                             annotated_pheno_data,
                             annotation_data,
                             annotation_version,
                             name,
                             normalization_method,
                             description,
                             xref)


# -----------------
# DGE & executions
# -----------------

def run_dge(session,
            roger_wd_dir,
            contrast,
            design,
            dataset,
            algorithm: DGEAlgorithm):
    model = query_dge_models(session, contrast, design, dataset, algorithm.name,
                             DGEmodel).one_or_none()
    if model is not None:
        raise ROGERUsageError("A model for %s:%s:%s has already been generated by the method '%s'"
                              % (dataset, design, contrast, algorithm.name))

    print("Retrieving data from database")
    contrast_data = get_contrast(session, contrast, design, dataset)
    design_data = contrast_data.Design
    ds_data = design_data.DataSet

    feature_data = ds_data.feature_data

    print("Performing differential gene expression analysis using %s" % algorithm.name)
    contrast_matrix = contrast_data.contrast_matrix
    dge_result = algorithm.exec_dge(ds_data.ExprsWC,
                                    feature_data,
                                    design_data,
                                    contrast_matrix)

    print("Persisting model information")
    method = session.query(DGEmethod).filter(DGEmethod.Name == algorithm.name).one()

    dge_method_sub_dir = "%d_%d" % (contrast_data.ID, method.ID)

    dge_models_path = os.path.join(roger_wd_dir, DGE_MODEL_SUB_FOLDER)
    dge_model_path = os.path.join(dge_models_path, dge_method_sub_dir)
    if not os.path.exists(dge_model_path):
        os.makedirs(dge_model_path)

    input_obj_file = os.path.abspath(os.path.join(dge_model_path, "limma_input_obj.rds"))
    base.saveRDS(dge_result.input_obj, file=input_obj_file)

    fit_obj_file = os.path.abspath(os.path.join(dge_model_path, "limma_fit_obj"))
    base.saveRDS(dge_result.fit_obj, file=fit_obj_file)

    dge_model = DGEmodel(ContrastID=contrast_data.ID,
                         DGEmethodID=method.ID,
                         InputObjFile=input_obj_file,
                         FitObjFile=fit_obj_file,
                         MethodDescription=dge_result.method_description)

    session.add(dge_model)
    session.flush()

    print("Persisting feature subsets")
    feature_subset = pd.DataFrame({"FeatureIndex": feature_data["FeatureIndex"],
                                   "DataSetID": ds_data.ID,
                                   "ContrastID": contrast_data.ID,
                                   "DGEmethodID": method.ID,
                                   "IsUsed": dge_result.used_feature_list,
                                   "Description": "Default filtering by '%s'" % algorithm.name})
    insert_data_frame(session, feature_subset, FeatureSubset.__table__)

    dge_tbl = dge_result.dge_table \
        .join(contrast_data.contrast_columns.set_index("Name"), on="Contrast", rsuffix="_C") \
        .join(feature_data.set_index("FeatureIndex"), on="FeatureIndex", rsuffix="_F")

    dgetable = pd.DataFrame({'ContrastColumnID': dge_tbl["ID"],
                             'FeatureIndex': dge_tbl["FeatureIndex"],
                             "ContrastID": contrast_data.ID,
                             "DGEmethodID": method.ID,
                             'DataSetID': dge_tbl["DataSetID"],
                             'AveExprs': dge_tbl["AveExpr"],
                             'Statistic': dge_tbl["t"],
                             'LogFC': dge_tbl["logFC"],
                             'PValue': dge_tbl["PValue"],
                             'FDR': dge_tbl["FDR"]})
    insert_data_frame(session, dgetable, DGEtable.__table__)
    session.commit()


def get_algorithm(name) -> DGEAlgorithm:
    algorithm_dict = {algo.name: algo for algo in [cls() for cls in all_subclasses(DGEAlgorithm)]}
    if name not in algorithm_dict:
        raise ROGERUsageError("Algorithm '%s' does not exist" % name)
    return algorithm_dict[name]
