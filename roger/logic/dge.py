import tempfile
from typing import Type

from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from rpy2 import robjects
from collections import OrderedDict
import pandas as pd
import os.path
import shutil

from roger.persistence.dge import get_ds
from roger.persistence.schema import DGEmethod, FeatureMapping, DGEtable, DGEmodel, \
    DataSet, FeatureSubset
import roger.logic.geneanno
import roger.persistence.geneanno
import roger.persistence.dge
from roger.exception import ROGERUsageError
from roger.util import get_or_guess_name, parse_gct

DATASET_SUB_FOLDER = "dataset"
DGE_MODEL_SUB_FOLDER = "dge_model"

pandas2ri.activate()

base = importr("base")
biobase = importr("Biobase")


def annotate_ds_pheno_data(gct_data, pheno_file):
    # TODO: Move this to separate
    # design_data = pd.read_table(design_file, sep='\t', index_col=0)
    # groups = design_data.apply(lambda row: "_".join(["%s.%d" % (key, value) for (key, value) in row.items()]), axis=1)
    pheno_data = pd.DataFrame()
    if pheno_file is not None:
        pheno_data = pd.read_table(pheno_file, sep='\t', index_col=0)

    pheno_data["ROGER_SampleName"] = list(gct_data)
    pheno_data["ROGER_SampleIndex"] = list(range(0, pheno_data.shape[0]))
    # pheno_data["_SampleGroup"] = groups.values
    return pheno_data


def perform_limma(exprs_file: str,
                  feature_anno: pd.DataFrame,
                  design_data: pd.DataFrame,
                  contrast_matrix: pd.DataFrame,
                  use_weighted: bool = False):
    methods = importr("methods")
    limma = importr("limma")
    ribios_io = importr("ribiosIO")
    ribios_roger = importr("ribiosROGER")

    # TODO check of this is actually present or not
    exprs_data = ribios_io.read_exprs_matrix(exprs_file)

    # conts_names_backup < - colnames(contrast_data)
    # colnames(contrast_data) < - make.names(colnames(contrast_data))
    eset = methods.new("ExpressionSet", exprs=exprs_data)

    # Yep, this is how you call replacement functions from python
    eset = biobase.__dict__["fData<-"](eset, feature_anno)

    weights = robjects.vectors.IntVector([1] * base.ncol(exprs_data)[0])
    if use_weighted:
        # doLog("Estimating weights by linear model", level=1L)
        weights = limma.arrayWeights(eset, design=design_data)

    eset_fit = limma.lmFit(object=eset, design=design_data, weights=weights)
    eset_fit = limma.contrasts_fit(eset_fit, contrast_matrix)
    eset_fit = limma.eBayes(eset_fit)

    dge_tbl = pandas2ri.ri2py(ribios_roger.limmaDgeTable(eset_fit))

    used_feature_names = robjects.conversion.ri2py(base.rownames(eset_fit.rx2("genes")))

    # TODO: return result type instead of a tuple
    return eset, eset_fit, dge_tbl, used_feature_names


def perform_edger(exprs_file: str,
                  feature_anno: pd.DataFrame,
                  design_data: pd.DataFrame,
                  contrast_matrix: pd.DataFrame):
    ribios_io = importr("ribiosIO")
    ribios_expression = importr("ribiosExpression")
    ribios_ngs = importr("ribiosNGS")
    utils = importr("utils")

    design_file, design_file_path = tempfile.mkstemp()
    fdf_file, fdf_file_path = tempfile.mkstemp()
    contrast_file, contrast_file_path = tempfile.mkstemp()

    design_data.to_csv(design_file_path, sep="\t")
    contrast_matrix.to_csv(contrast_file_path, sep="\t")
    feature_anno.to_csv(fdf_file_path, sep="\t")

    # TODO check of this is actually present or not
    exprs_data = ribios_io.read_exprs_matrix(exprs_file)

    descon = ribios_expression.parseDesignContrast(designFile=design_file_path, contrastFile=contrast_file_path)

    edger_input = ribios_ngs.EdgeObject(exprs_data, descon)

    slot = edger_input.slots["dgeList"]
    slot.rx2["genes"] = ribios_io.readTable(fdf_file_path)
    slot.rx2["annotation"] = "GeneID"
    edger_input.slots["dgeList"] = slot

    edger_result = ribios_ngs.dgeWithEdgeR(edger_input)

    dge_file, dge_file_path = tempfile.mkstemp()
    utils.write_table(ribios_ngs.dgeTable(edger_result), dge_file_path, sep="\t")
    dge_tbl = pd.read_table(dge_file_path)
    dge_tbl = dge_tbl.rename(index=str, columns={"logCPM": "AveExpr",
                                                 "LR": "t"})

    used_feature_names = robjects.conversion.ri2py(biobase.featureNames(edger_result))

    # TODO: return result type instead of a tuple
    return edger_result.do_slot("dgeList"), edger_result.do_slot("dgeGLM"), dge_tbl, used_feature_names


# ---------------
# Datasets
# ---------------


# TODO: Separate between annotation and actual persistence
def add_ds(session,
           roger_wd_dir,
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
    species_list = roger.persistence.geneanno.list_species(session)
    if species_list[species_list.TaxID == tax_id].empty:
        raise ROGERUsageError('Unknown taxon id: %s' % tax_id)

    if session.query(DataSet).filter(DataSet.Name == name).one_or_none() is not None:
        raise ROGERUsageError("Data set with name '%s' already exists" % name)

    # Read and annotate data
    target_for_annotation = exprs_file

    gct_data = parse_gct(file_path=target_for_annotation)
    print("Annotating features")
    (feature_data, annotation_version) = roger.logic.geneanno.annotate(session, gct_data, tax_id, symbol_type)

    print("Persisting data set")
    # Persist data
    datasets_path = os.path.join(roger_wd_dir, DATASET_SUB_FOLDER)
    dataset_path = os.path.join(datasets_path, name)
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    wc_exprs_file = None
    if exprs_file is not None:
        wc_exprs_file = os.path.abspath(os.path.join(dataset_path, "exprs.gct"))
        shutil.copy(exprs_file, wc_exprs_file)

    wc_pheno_file = os.path.abspath(os.path.join(dataset_path, "pheno.tsv"))
    pheno_data = annotate_ds_pheno_data(gct_data, pheno_file)
    pheno_data.to_csv(wc_pheno_file, sep="\t")

    dataset_entry = ds_type(Name=name,
                            GeneAnnotationVersion=annotation_version,
                            Description=description,
                            FeatureCount=gct_data.shape[0],
                            SampleCount=gct_data.shape[1],
                            ExprsWC=wc_exprs_file,
                            ExprsSrc=exprs_file,
                            NormalizationMethod=normalization_method,
                            PhenoWC=wc_pheno_file,
                            PhenoSrc=pheno_file,
                            TaxID=tax_id,
                            Xref=xref,
                            CreatedBy=roger.util.get_current_user_name(),
                            CreationTime=roger.util.get_current_datetime())
    session.add(dataset_entry)
    session.flush()
    feature_data["DataSetID"] = dataset_entry.ID
    roger.util.insert_data_frame(session, feature_data, FeatureMapping.__table__)
    session.commit()
    return name


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

    contrast_data = roger.persistence.dge.get_contrast(session, contrast, design, dataset)
    design_data = contrast_data.Design
    ds_data = design_data.DataSet

    feature_data = ds_data.feature_data

    print("Performing differential gene expression analysis using %s" % algorithm_name)
    contrast_matrix = contrast_data.contrast_matrix
    design_matrix = design_data.design_matrix
    eset, eset_fit, dge_tbl, used_feature_names = algorithm(ds_data.ExprsWC,
                                                            feature_data,
                                                            design_matrix,
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
    feature_subset = feature_data[feature_data['Feature'].isin(used_feature_names)]
    feature_subset = feature_data.set_index("Name").join(feature_subset)
    is_used = feature_subset["Feature"].apply(lambda x: True if type(x).__name__ == "str" else False)

    feature_subset = pd.DataFrame({"FeatureIndex": feature_subset["FeatureIndex"],
                                   "DataSetID": ds_data.ID,
                                   "ContrastID": contrast_data.ID,
                                   "DGEmethodID": method.ID,
                                   "IsUsed": is_used,
                                   "Description": "Default filtering by '%s'" % algorithm_name})
    roger.util.insert_data_frame(session, feature_subset, FeatureSubset.__table__)

    print("Persisting DGE table")
    dge_tbl = dge_tbl.join(contrast_data.contrast_columns.set_index("Name"), on="Contrast", rsuffix="_C") \
        .join(feature_data.set_index("Name"), on="Feature", rsuffix="_F")
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
    roger.util.insert_data_frame(session, dgetable, DGEtable.__table__)
    session.commit()
