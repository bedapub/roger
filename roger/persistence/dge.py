import os.path
import shutil
from typing import Type

from pandas import DataFrame, read_table
import numpy as np

import roger.util

from roger.persistence.schema import DGEmethod, DataSet, Design, SampleSubset, Contrast, ContrastColumn, \
    FeatureMapping, DGEmodel
from roger.exception import ROGERUsageError
from roger.util import as_data_frame, silent_remove, silent_rmdir, get_or_guess_name, get_current_user_name, \
    get_current_datetime, insert_data_frame

DATASET_SUB_FOLDER = "dataset"


class DataSetProperties(object):
    """This class is used as encapsulate parameters / properties into one class"""

    def __init__(self,
                 ds_type: Type[DataSet],
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
                 xref):
        self.ds_type = ds_type
        self.tax_id = tax_id
        self.exprs_file = exprs_file
        self.pheno_file = pheno_file
        self.exprs_data = exprs_data
        self.annotated_pheno_data = annotated_pheno_data
        self.annotation_data = annotation_data
        self.annotation_version = annotation_version
        self.name = name
        self.normalization_method = normalization_method
        self.description = description
        self.xref = xref


# --------------------------
# DGE methods
# --------------------------

def list_methods(session):
    return as_data_frame(session.query(DGEmethod.Name, DGEmethod.Description, DGEmethod.Version))


def add_method(session, name, description, version):
    method = DGEmethod(Name=name, Description=description, Version=version)
    session.add(method)
    session.commit()


def delete_method(session, name):
    # Check if DGE method is already preset in the database
    gse_methods = list_methods(session)
    if gse_methods[gse_methods.Name == name].empty:
        raise ROGERUsageError('DGE method does not exist in database: %s' % name)

    session.query(DGEmethod).filter(DGEmethod.Name == name).delete()
    session.commit()


# --------------------------
# Data sets
# --------------------------

def get_ds(session, name) -> DataSet:
    ds = session.query(DataSet).filter(DataSet.Name == name).one_or_none()
    if ds is None:
        raise ROGERUsageError("Data set with name '%s' does not exist" % name)
    return ds


def list_ds(session):
    return as_data_frame(session.query(DataSet.Name,
                                       DataSet.Type,
                                       DataSet.FeatureCount,
                                       DataSet.SampleCount,
                                       DataSet.CreatedBy,
                                       DataSet.Xref))


def add_ds(session,
           roger_wd_dir,
           ds_prop: DataSetProperties):
    # Persist data
    datasets_path = os.path.join(roger_wd_dir, DATASET_SUB_FOLDER)
    dataset_path = os.path.join(datasets_path, ds_prop.name)
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    wc_exprs_file = os.path.abspath(os.path.join(dataset_path, "exprs.gct"))
    shutil.copy(ds_prop.exprs_file, wc_exprs_file)

    wc_pheno_file = os.path.abspath(os.path.join(dataset_path, "pheno.tsv"))
    ds_prop.annotated_pheno_data.to_csv(wc_pheno_file, sep="\t")

    dataset_entry = ds_prop.ds_type(Name=ds_prop.name,
                                    GeneAnnotationVersion=ds_prop.annotation_version,
                                    Description=ds_prop.description,
                                    FeatureCount=ds_prop.exprs_data.shape[0],
                                    SampleCount=ds_prop.exprs_data.shape[1],
                                    ExprsWC=wc_exprs_file,
                                    ExprsSrc=ds_prop.exprs_file,
                                    NormalizationMethod=ds_prop.normalization_method,
                                    PhenoWC=wc_pheno_file,
                                    PhenoSrc=ds_prop.pheno_file,
                                    TaxID=ds_prop.tax_id,
                                    Xref=ds_prop.xref,
                                    CreatedBy=roger.util.get_current_user_name(),
                                    CreationTime=roger.util.get_current_datetime())
    session.add(dataset_entry)
    session.flush()
    ds_prop.annotation_data["DataSetID"] = dataset_entry.ID
    roger.util.insert_data_frame(session, ds_prop.annotation_data, FeatureMapping.__table__)
    session.commit()
    return dataset_entry


def delete_ds(session, name):
    ds_entiry = get_ds(session, name)
    silent_remove(ds_entiry.PhenoWC)
    silent_remove(ds_entiry.ExprsWC)
    silent_rmdir(os.path.dirname(ds_entiry.ExprsWC))

    session.delete(ds_entiry)
    session.commit()


# -----------------
# Design Matrix
# -----------------

def query_design(session, design_name, ds_name) -> Design:
    return session.query(Design) \
        .filter(Design.DataSetID == DataSet.ID) \
        .filter(Design.Name == design_name and DataSet.Name == ds_name)


def get_design(session, design_name, ds_name) -> Design:
    design = query_design(session, design_name, ds_name).one_or_none()
    if design is None:
        raise ROGERUsageError("Design of data set '%s' with name '%s' does not exist" % (ds_name, design_name))
    return design


def list_design(session, ds_name=None):
    q = session.query(Design.Name,
                      Design.Description,
                      DataSet.Name.label("DataSet"),
                      Design.VariableCount,
                      Design.CreatedBy) \
        .filter(Design.DataSetID == DataSet.ID)
    if ds_name is not None:
        q = q.filter(DataSet.Name == ds_name)
    return as_data_frame(q)


def remove_design(session, design_name, ds_name):
    design = get_design(session, design_name, ds_name)
    session.query(Design).filter(Design.ID == design.ID).delete()
    session.commit()


def __check_matrix(ref_columns, matrix, matrix_name, ref_list_name):
    if len(ref_columns) != matrix.shape[0]:
        raise ROGERUsageError("Number of rows in %s does not match the number of %s: %d vs %d"
                              % (matrix_name, ref_list_name, len(ref_columns), matrix.shape[0]))
    if matrix.index.dtype.name == "object" and set(matrix.index) != set(ref_columns):
        raise ROGERUsageError("Row names of %s and %s do not match" % (matrix_name, ref_list_name))

    for col_name in matrix.columns:
        if not np.issubdtype(matrix[col_name].dtype, np.integer):
            raise ROGERUsageError("Column '%s' is not an integer type" % col_name)


def check_design_matrix(ref_columns, matrix):
    __check_matrix(ref_columns, matrix, "design matrix", "sample names")


def check_contrast_matrix(ref_columns, matrix):
    __check_matrix(ref_columns, matrix, "contrast matrix", "design matrix column names")


# TODO: Method to pass DESIGN / work with matrix:
# 1 directly add TSV file with no extra information
# 2 pass TSV and apply SVA for covariance detection
# 3 pass TSV matrix + covariance information from R session (by using model.matrix methods and friends)
# (4 pass matrix and covariance information as JSON file [NOT recommended])
def add_design(session, design_file, dataset_name, name=None, description=None):
    ds = get_ds(session, dataset_name)

    name = get_or_guess_name(name, design_file)

    design = query_design(session, name, dataset_name).one_or_none()
    if design is not None:
        raise ROGERUsageError("Design of data set '%s' with name '%s' already exist" % (dataset_name, name))

    design_data = read_table(design_file, sep='\t', index_col=0)
    check_design_matrix(ds.exprs_data.columns, design_data)

    pheno_data = ds.pheno_data
    # TODO make this customizable by user
    sample_subset = DataFrame({"SampleIndex": range(0, pheno_data.shape[0]),
                               "IsUsed": True,
                               "Description": "ROGER currently only support designs where all samples are used."})

    # TODO make this customizable by user
    json_obj = [{"columnName": col_name,
                 "isCovariate": False,
                 "values": design_data[col_name].values.tolist()}
                for col_name in design_data.columns]

    design_entry = Design(DataSetID=ds.ID,
                          VariableCount=sample_subset[sample_subset.IsUsed].shape[0],
                          Name=name,
                          Description=description,
                          DesignMatrix=json_obj,
                          CreatedBy=get_current_user_name(),
                          CreationTime=get_current_datetime())
    session.add(design_entry)
    session.flush()

    sample_subset["DesignID"] = design_entry.ID
    insert_data_frame(session, sample_subset, SampleSubset.__table__)

    session.commit()
    return name


# -----------------
# Contrast Matrix
# -----------------

def query_contrast(session, contrast_name, design_name, ds_name) -> Contrast:
    return session.query(Contrast) \
        .filter(Contrast.DesignID == Design.ID) \
        .filter(Design.DataSetID == DataSet.ID) \
        .filter(Contrast.Name == contrast_name and Design.Name == design_name and DataSet.Name == ds_name)


def get_contrast(session, contrast_name, design_name, ds_name) -> Contrast:
    design = query_contrast(session, contrast_name, design_name, ds_name).one_or_none()
    if design is None:
        raise ROGERUsageError("Contrast of design '%s' with name '%s' does not exist" % (design_name, contrast_name))
    return design


def list_contrast(session, design_name=None, ds_name=None):
    q = session.query(Contrast.Name,
                      Contrast.Description,
                      Design.Name.label("Design"),
                      DataSet.Name.label("DataSet"),
                      Contrast.CreatedBy) \
        .filter(Contrast.DesignID == Design.ID) \
        .filter(Design.DataSetID == DataSet.ID)
    if design_name is not None:
        q = q.filter(Design.Name == design_name)
    if ds_name is not None:
        q = q.filter(DataSet.Name == ds_name)
    return as_data_frame(q)


def remove_contrast(session, contrast_name, design_name, ds_name):
    contrast = get_contrast(session, contrast_name, design_name, ds_name)
    session.query(Contrast).filter(Contrast.ID == contrast.ID).delete()
    session.commit()


def add_contrast(session, contrast_file, design_name, dataset_name, name=None, description=None):
    design = get_design(session, design_name, dataset_name)

    name = get_or_guess_name(name, contrast_file)

    if query_contrast(session, name, design_name, dataset_name).one_or_none() is not None:
        raise ROGERUsageError("Contrast '%s' already exist in '%s'" % (name, design_name))

    contrast = Contrast(DesignID=design.ID,
                        Name=name,
                        Description=description,
                        CreatedBy=get_current_user_name(),
                        CreationTime=get_current_datetime())
    session.add(contrast)
    session.flush()

    contrast_data = read_table(contrast_file, sep='\t', index_col=0)
    check_contrast_matrix(design.design_matrix.columns, contrast_data)

    contrast_cols = contrast_data.columns
    contrast_table = DataFrame({"ContrastID": contrast.ID,
                                "Name": contrast_cols,
                                "Description": contrast_cols,
                                "ColumnData": [contrast_data[col_name].values.tolist() for col_name in contrast_cols]})

    insert_data_frame(session, contrast_table, ContrastColumn.__table__)

    session.commit()
    return name


# -----------------
# Contrast Matrix
# -----------------


def query_dge_models(session, contrast_name, design_name, dataset_name, method_name, *query_attr_args):
    q = session.query(*query_attr_args) \
        .filter(Contrast.DesignID == Design.ID) \
        .filter(Design.DataSetID == DataSet.ID) \
        .filter(DGEmodel.ContrastID == Contrast.ID) \
        .filter(DGEmodel.DGEmethodID == DGEmethod.ID)
    if contrast_name is not None:
        q = q.filter(Contrast.Name == contrast_name)
    if design_name is not None:
        q = q.filter(Design.Name == design_name)
    if dataset_name is not None:
        q = q.filter(DataSet.Name == dataset_name)
    if method_name is not None:
        q = q.filter(DGEmethod.Name == method_name)
    return q


def get_dge_model(session, contrast_name, design_name, dataset_name, method_name) -> DGEmodel:
    model = query_dge_models(session, contrast_name, design_name, dataset_name, method_name,
                             DGEmodel).one_or_none()
    if model is None:
        raise ROGERUsageError("Model for %s:%s:%s does not exists" % (dataset_name, design_name, contrast_name))
    return model


def list_dge_models(session, contrast_name, design_name, dataset_name, method_name):
    q = query_dge_models(session, contrast_name, design_name, dataset_name, method_name,
                         DataSet.Name.label("DataSet"),
                         Design.Name.label("Design"),
                         Contrast.Name.label("Contrast"),
                         DGEmethod.Name.label("Method"))
    return as_data_frame(q)


def remove_dge_model(session, contrast, design, dataset, method):
    model_entiry = get_dge_model(session, contrast, design, dataset, method)
    silent_remove(model_entiry.InputObjFile)
    silent_remove(model_entiry.FitObjFile)
    silent_rmdir(os.path.dirname(model_entiry.FitObjFile))

    session.delete(model_entiry)
    session.commit()
