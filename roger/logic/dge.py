import tempfile
from typing import Type

from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from rpy2 import robjects
import pandas as pd
import os.path

from roger.exception import ROGERUsageError
from roger.logic.geneanno import annotate

from roger.persistence.dge import ROGER_SAMPLE_NAME, DataSetProperties, get_contrast
from roger.persistence.geneanno import list_species
from roger.persistence.schema import DGEmethod, DGEtable, DGEmodel, \
    DataSet, FeatureSubset, Design
from roger.util import get_or_guess_name, parse_gct, insert_data_frame, read_df

DGE_MODEL_SUB_FOLDER = "dge_model"

pandas2ri.activate()

base = importr("base")
biobase = importr("Biobase")


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


def perform_limma(exprs_file: str,
                  feature_anno: pd.DataFrame,
                  design: Design,
                  contrast_matrix: pd.DataFrame,
                  use_weighted: bool = False):
    methods = importr("methods")
    limma = importr("limma")
    ribios_io = importr("ribiosIO")
    ribios_roger = importr("ribiosROGER")

    design_data = design.design_matrix

    exprs_data = ribios_io.read_exprs_matrix(exprs_file)

    eset = methods.new("ExpressionSet", exprs=exprs_data)

    # TODO We drop Description column here, because it might cause warnings
    eset = biobase.__dict__["fData<-"](eset, feature_anno.drop(columns=['Description']))

    weights = robjects.vectors.IntVector([1] * base.ncol(exprs_data)[0])
    if use_weighted:
        weights = limma.arrayWeights(eset, design=design_data)

    eset_fit = limma.lmFit(object=eset, design=design_data, weights=weights)
    eset_fit = limma.contrasts_fit(eset_fit, contrast_matrix)
    eset_fit = limma.eBayes(eset_fit)

    dge_tbl = pandas2ri.ri2py(ribios_roger.limmaDgeTable(eset_fit))

    used_names = robjects.conversion.ri2py(base.rownames(eset_fit.rx2("genes")))

    used_features = feature_anno['FeatureIndex'].isin(used_names)

    # TODO: return result type instead of a tuple
    return eset, eset_fit, dge_tbl, used_features


def perform_edger(exprs_file: str,
                  feature_anno: pd.DataFrame,
                  design: Design,
                  contrast_matrix: pd.DataFrame):
    ribios_io = importr("ribiosIO")
    ribios_expression = importr("ribiosExpression")
    ribios_ngs = importr("ribiosNGS")
    utils = importr("utils")

    design_file, design_file_path = tempfile.mkstemp()
    contrast_file, contrast_file_path = tempfile.mkstemp()
    fdf_file, fdf_file_path = tempfile.mkstemp()

    design_matrix = design.design_matrix
    design_matrix.index = range(1, len(design_matrix.index) + 1)
    design_matrix.to_csv(design_file_path, sep="\t")
    contrast_matrix.to_csv(contrast_file_path, sep="\t")
    feature_anno.to_csv(fdf_file_path, sep="\t")

    # TODO how to pass the other additional arguments???
    exprs_data = ribios_io.read_exprs_matrix(exprs_file)

    descon = ribios_expression.parseDesignContrast(designFile=design_file_path,
                                                   contrastFile=contrast_file_path,
                                                   sampleGroups=",".join(design.SampleGroups),
                                                   groupLevels=",".join(design.SampleGroupLevels),
                                                   dispLevels=robjects.r("NULL"),
                                                   contrasts=robjects.r("NULL"),
                                                   expSampleNames=base.colnames(exprs_data))

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

    print(len(robjects.conversion.ri2py(biobase.featureNames(edger_result))))

    # TODO: return result type instead of a tuple
    return edger_result.do_slot("dgeList"), edger_result.do_slot("dgeGLM"), dge_tbl, used_features


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
            algorithm,
            algorithm_name="limma"):
    print("Retrieving data from database")

    contrast_data = get_contrast(session, contrast, design, dataset)
    design_data = contrast_data.Design
    ds_data = design_data.DataSet

    feature_data = ds_data.feature_data

    print("Performing differential gene expression analysis using %s" % algorithm_name)
    contrast_matrix = contrast_data.contrast_matrix
    eset, eset_fit, dge_tbl, used_features = algorithm(ds_data.ExprsWC,
                                                       feature_data,
                                                       design_data,
                                                       contrast_matrix)

    print("Persisting model information")
    # TODO why are methods stored in table anyway?
    method = session.query(DGEmethod).filter(DGEmethod.Name == algorithm_name).one()

    dge_method_sub_dir = "%d_%d" % (contrast_data.ID, method.ID)

    dge_models_path = os.path.join(roger_wd_dir, DGE_MODEL_SUB_FOLDER)
    dge_model_path = os.path.join(dge_models_path, dge_method_sub_dir)
    if not os.path.exists(dge_model_path):
        os.makedirs(dge_model_path)

    input_obj_file = os.path.abspath(os.path.join(dge_model_path, "input_obj.rds"))
    base.saveRDS(eset, file=input_obj_file)

    fit_obj_file = os.path.abspath(os.path.join(dge_model_path, "fit_obj.rds"))
    base.saveRDS(eset_fit, file=fit_obj_file)

    dge_model = DGEmodel(ContrastID=contrast_data.ID,
                         DGEmethodID=method.ID,
                         InputObjFile=input_obj_file,
                         FitObjFile=fit_obj_file)

    session.add(dge_model)
    session.flush()

    print("Persisting feature subsets")
    feature_subset = pd.DataFrame({"FeatureIndex": feature_data["FeatureIndex"],
                                   "DataSetID": ds_data.ID,
                                   "ContrastID": contrast_data.ID,
                                   "DGEmethodID": method.ID,
                                   "IsUsed": used_features,
                                   "Description": "Default filtering by '%s'" % algorithm_name})
    insert_data_frame(session, feature_subset, FeatureSubset.__table__)

    print("Persisting DGE table")
    dge_tbl = dge_tbl.join(contrast_data.contrast_columns.set_index("Name"), on="Contrast", rsuffix="_C") \
        .join(feature_data.set_index("Name"), on="Name", rsuffix="_F")
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
