from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from rpy2 import robjects
import pandas as pd
import numpy as np
import os.path
import shutil

from roger.persistence.schema import DataSet, Design, DGEmethod, Contrast, FeatureMapping, DGEtable, DGEmodel
import roger.logic.geneanno
import roger.util
import roger.persistence.geneanno
import roger.persistence.dge
from roger.exception import ROGERUsageError

DATASET_SUB_FOLDER = "dataset"
DGE_MODEL_SUB_FOLDER = "dge_model"

pandas2ri.activate()

base = importr("base")
ribios_io = importr("ribiosIO")
ribios_util = importr("ribiosUtils")
ribios_roger = importr("ribiosROGER")
ribios_epression = importr("ribiosExpression")
methods = importr("methods")
biobase = importr("Biobase")
limma = importr("limma")


def parse_pheno_data(design_file, gct_data):
    design_data = pd.read_table(design_file, sep='\t', index_col=0)
    groups = design_data.apply(lambda row: "_".join(["%s.%d" % (key, value) for (key, value) in row.items()]), axis=1)
    pheno_data = pd.DataFrame({"Sample": list(gct_data)})

    pheno_data["_DatasetSampleIndex"] = range(1, pheno_data.shape[0] + 1)
    pheno_data["_Sample"] = list(gct_data)
    pheno_data["_SampleGroup"] = groups.values
    return pheno_data


def add_ds(session,
           roger_wd_dir,
           dataset_file,
           design_file,
           tax_id,
           symbol_type,
           exprs_type,
           ds_name,
           description,
           xref):
    # Input checking
    species_list = roger.persistence.geneanno.list_species(session)
    if species_list[species_list.TaxID == tax_id].empty:
        raise ROGERUsageError('Unknown taxon id: %s' % tax_id)

    if ds_name is None:
        ds_name = os.path.splitext(os.path.basename(dataset_file))[0]

    # Read and annotate data
    gct_data = roger.util.parse_gct(file_path=dataset_file)
    pheno_data = parse_pheno_data(design_file, gct_data)
    print("Annotating features")
    (feature_data, annotation_version) = roger.logic.geneanno.annotate(session, gct_data, tax_id, symbol_type)

    print("Persisting data set")
    # Persist data
    datasets_path = os.path.join(roger_wd_dir, DATASET_SUB_FOLDER)
    dataset_path = os.path.join(datasets_path, ds_name)
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    exprs_file = os.path.abspath(os.path.join(dataset_path, "exprs.gct"))
    shutil.copy(dataset_file, exprs_file)

    pheno_file = os.path.abspath(os.path.join(dataset_path, "pheno.tsv"))
    pheno_data.to_csv(pheno_file, sep="\t", index=False)

    dataset_entry = DataSet(Name=ds_name,
                            GeneAnnotationVersion=annotation_version,
                            Description=description,
                            FeatureCount=feature_data.shape[0],
                            SampleCount=gct_data.shape[1],
                            ExprsWC=exprs_file,
                            ExprsSrc=exprs_file,
                            NormalizedExprsWC=exprs_file,
                            NormalizedExprsSrc=exprs_file,
                            ExprsType=exprs_type,
                            PhenoWC=pheno_file,
                            PhenoSrc=pheno_file,
                            # TODO
                            FeatureType="transcriptome",
                            TaxID=tax_id,
                            Xref=xref,
                            # TODO
                            URL="",
                            CreatedBy=roger.util.get_current_user_name(),
                            CreationTime=roger.util.get_current_datetime())
    session.add(dataset_entry)
    session.flush()
    feature_data["DataSetID"] = dataset_entry.ID
    session.commit()
    roger.util.insert_data_frame(session, feature_data, FeatureMapping.__tablename__)
    return dataset_entry


def perform_limma(exprs_data, fdf, design_data, contrast_data, use_weighted=False):
    # conts_names_backup < - colnames(contrast_data)
    # colnames(contrast_data) < - make.names(colnames(contrast_data))
    eset = methods.new("ExpressionSet", exprs=exprs_data)

    # fData(x) <- y
    # x$fData <- y ; return x
    # feature
    # fData(eset) <- feature
    # names(x) <- 1:10

    # Yep, this is how you call replacement functions from python
    eset = biobase.__dict__["fData<-"](eset, fdf)

    weights = robjects.vectors.IntVector([1] * base.ncol(exprs_data)[0])
    if use_weighted:
        # doLog("Estimating weights by linear model", level=1L)
        weights = limma.arrayWeights(eset, design=design_data)

    eset_fit = limma.lmFit(object=eset, design=design_data, weights=weights)
    eset_fit = limma.contrasts_fit(eset_fit, contrast_data)
    eset_fit = limma.eBayes(eset_fit)
    return eset, eset_fit


def r_blob(data):
    return memoryview(np.array([x for x in ribios_roger.blobs(data)[0]]))


def run_dge(session, roger_wd_dir, algorithm, dataset, design, contrast, design_name):
    print("Parsing data")
    if algorithm != "limma":
        raise ROGERUsageError("Only limma is supported for now")

    ds = roger.persistence.dge.get_ds(session, dataset)
    design_data = pd.read_table(design, sep='\t', index_col=0)
    contrast_data = pd.read_table(contrast, sep='\t', index_col=0)

    feature_data = ds.feature_data
    from collections import OrderedDict
    fdf = pd.DataFrame(OrderedDict([("Feature", feature_data["Name"]),
                                    ("GeneID", feature_data["RogerGeneIndex"]),
                                    ("index", feature_data["Name"])])).set_index("index")
    exprs_data = ribios_io.read_exprs_matrix(ds.ExprsWC)
    # limma
    print("Performing differential gene expression analysis using limma")
    (eset, eset_fit) = perform_limma(exprs_data, fdf, design_data, contrast_data)

    print("Persisting design information")
    feature_names = robjects.conversion.ri2py(base.rownames(eset_fit.rx2("genes")))
    feature_subset = fdf[fdf['Feature'].isin(feature_names)]
    feature_subset = feature_data.set_index("Name").join(feature_subset)
    is_used = feature_subset["Feature"].apply(lambda x: True if type(x).__name__ == "str" else False)

    feature_subset = pd.DataFrame({"DatasetFeatureIndex": feature_subset["FeatureIndex"],
                                   "IsUsed": is_used,
                                   "Description": "Default filtering by limma"})

    sample_subset = pd.DataFrame({"DatasetSampleIndex": range(1, robjects.conversion.ri2py(base.ncol(exprs_data))[0]),
                                  "IsUsed": True,
                                  "Description": "ROGER currently only support designs where all samples are used."})
    if design_name is None:
        design_name = os.path.splitext(os.path.basename(design))[0]

    design_entry = Design(DataSetID=ds.ID,
                          VariableCount=sample_subset[sample_subset.IsUsed].shape[0],
                          Name=design_name,
                          Description="limma script default design",
                          # TODO cannot store as R blob
                          FeatureSubset=r_blob(pandas2ri.py2ri(feature_subset)),
                          SampleSubset=r_blob(pandas2ri.py2ri(sample_subset)),
                          DesignMatrix=r_blob(ribios_epression.designMatrix(eset_fit)),
                          CreatedBy=roger.util.get_current_user_name(),
                          CreationTime=roger.util.get_current_datetime())
    session.add(design_entry)
    session.flush()
    session.commit()

    print("Persisting contrast information")
    contrast_matrix_r = ribios_epression.contrastMatrix(eset_fit)
    contrast_cols = robjects.conversion.ri2py(base.colnames(contrast_matrix_r))
    contrast_table = pd.DataFrame({"DesignID": design_entry.ID,
                                   "Name": contrast_cols,
                                   "Description": contrast_cols,
                                   "Contrast": [x for x in ribios_roger.serializeMatrixByCol(contrast_matrix_r)],
                                   "CreatedBy": roger.util.get_current_user_name(),
                                   "CreationTime": roger.util.get_current_datetime()})
    roger.util.insert_data_frame(session, contrast_table, Contrast.__tablename__)
    contrast_table = roger.util.as_data_frame(session.query(Contrast).filter(Contrast.DesignID == design_entry.ID))

    print("Persisting model information")
    method = session.query(DGEmethod).filter(DGEmethod.Name == "limma").all()[0]

    dge_method_sub_dir = "%d_%d" % (design_entry.ID, method.ID)

    dge_models_path = os.path.join(roger_wd_dir, DGE_MODEL_SUB_FOLDER)
    dge_model_path = os.path.join(dge_models_path, dge_method_sub_dir)
    if not os.path.exists(dge_model_path):
        os.makedirs(dge_model_path)

    input_obj_file = os.path.abspath(os.path.join(dge_model_path, "input_obj.rds"))
    base.saveRDS(eset, file=input_obj_file)

    fit_obj_file = os.path.abspath(os.path.join(dge_model_path, "fit_obj.rds"))
    base.saveRDS(eset_fit, file=fit_obj_file)

    dge_model = DGEmodel(DesignID=design_entry.ID,
                         DGEmethodID=method.ID,
                         InputObjFile=input_obj_file,
                         FitObjFile=fit_obj_file)

    session.add(dge_model)
    session.flush()
    session.commit()

    print("Persisting DGE results")
    dge_tbl = pandas2ri.ri2py(ribios_roger.limmaDgeTable(eset_fit))
    dge_tbl = dge_tbl.join(contrast_table.set_index("Name"), on="Contrast", rsuffix="_C") \
        .join(feature_data.set_index("Name"), on="Feature", rsuffix="_F")
    dgetable = pd.DataFrame({'ContrastID': dge_tbl["ID"],
                             'FeatureIndex': dge_tbl["FeatureIndex"],
                             'DataSetID': dge_tbl["DataSetID"],
                             'AveExprs': dge_tbl["AveExpr"],
                             'Statistic': dge_tbl["t"],
                             'LogFC': dge_tbl["logFC"],
                             'PValue': dge_tbl["PValue"],
                             'FDR': dge_tbl["FDR"]})
    roger.util.insert_data_frame(session, dgetable, DGEtable.__tablename__)
