import os.path
from pandas import DataFrame, read_table

from roger.persistence.schema import DGEmethod, DataSet, Design, SampleSubset, Contrast
from roger.exception import ROGERUsageError
import roger.util


# --------------------------
# DGE methods
# --------------------------


def list_methods(session):
    return roger.util.as_data_frame(session.query(DGEmethod.Name, DGEmethod.Description, DGEmethod.Version))


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
    return roger.util.as_data_frame(session.query(DataSet.Name,
                                                  DataSet.Type,
                                                  DataSet.FeatureCount,
                                                  DataSet.SampleCount,
                                                  DataSet.CreatedBy,
                                                  DataSet.Xref))


def delete_ds(session, name):
    ds_entiry = get_ds(session, name)
    roger.util.silent_remove(ds_entiry.PhenoWC)
    roger.util.silent_remove(ds_entiry.ExprsWC)
    roger.util.silent_remove(ds_entiry.NormalizedExprsWC)
    roger.util.silent_rmdir(os.path.dirname(ds_entiry.NormalizedExprsWC))

    session.query(DataSet).filter(DataSet.Name == name).delete()
    session.commit()


# -----------------
# Design Matrix
# -----------------

def query_design(session, ds_name, design_name) -> Design:
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
    return roger.util.as_data_frame(q)


def remove_design(session, design_name, ds_name):
    design = get_design(session, design_name, ds_name)
    session.query(Design).filter(Design.ID == design.ID).delete()
    session.commit()


# TODO: Method to pass DESIGN / work with matrix:
# 1 directly add TSV file with no extra information
# 2 pass TSV and apply SVA for covariance detection
# 3 pass TSV matrix + covariance information from R session (by using model.matrix methods and friends)
# (4 pass matrix and covariance information as JSON file [NOT recommended])
def add_design(session, dataset_name, design_file, name, description):
    ds = get_ds(session, dataset_name)

    design = query_design(session, name, dataset_name).one_or_none()
    if design is not None:
        raise ROGERUsageError("Design of data set '%s' with name '%s' already exist" % (dataset_name, name))

    design_data = read_table(design_file, sep='\t', index_col=0)

    pheno_data = ds.pheno_data
    # TODO make this customizable by user
    sample_subset = DataFrame({"SampleIndex": range(0, pheno_data.shape[0]),
                               "IsUsed": True,
                               "Description": "ROGER currently only support designs where all samples are used."})

    # TODO make this customizable by user
    json_obj = {col_name: {
        "isCovariate": False,
        "values": design_data[col_name].values.tolist()}
        for col_name in design_data.columns}

    design_entry = Design(DataSetID=ds.ID,
                          VariableCount=sample_subset[sample_subset.IsUsed].shape[0],
                          Name=name,
                          Description=description,
                          DesignMatrix=json_obj,
                          CreatedBy=roger.util.get_current_user_name(),
                          CreationTime=roger.util.get_current_datetime())
    session.add(design_entry)
    session.flush()

    sample_subset["DesignID"] = design_entry.ID
    roger.util.insert_data_frame(session, sample_subset, SampleSubset.__table__)

    session.commit()

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
        raise ROGERUsageError("Design of data set '%s' with name '%s' does not exist" % (ds_name, design_name))
    return design


def list_contrast(session, design_name=None, ds_name=None):
    q = session.query(Contrast.Name,
                      Design.Description,
                      DataSet.Name.label("DataSet"),
                      Design.VariableCount,
                      Design.CreatedBy) \
        .filter(Design.DataSetID == DataSet.ID)
    if design_name is not None:
        q = q.filter(Design.Name == design_name)
    if ds_name is not None:
        q = q.filter(DataSet.Name == ds_name)
    return roger.util.as_data_frame(q)


def remove_design(session, design_name, ds_name):
    design = get_design(session, design_name, ds_name)
    session.query(Design).filter(Design.ID == design.ID).delete()
    session.commit()


def add_contrast(session, contrast_file, design_name, dataset_name, name, description):
    design = get_design(session, design_name, dataset_name)

    contrast = Contrast(DesignID=design.ID,
                        Name=name,
                        Description=description,
                        CreatedBy=roger.util.get_current_user_name(),
                        CreationTime=roger.util.get_current_datetime())

    print("Persisting contrast information")
    contrast_matrix_r = ribios_epression.contrastMatrix(eset_fit)
    contrast_cols = robjects.conversion.ri2py(base.colnames(contrast_matrix_r))
    contrast_table = DataFrame({"DesignID": design_entry.ID,
                                   "Name": contrast_cols,
                                   "Description": contrast_cols,
                                   "Contrast": [x for x in ribios_roger.serializeMatrixByCol(contrast_matrix_r)],
                                   "CreatedBy": roger.util.get_current_user_name(),
                                   "CreationTime": roger.util.get_current_datetime()})
    roger.util.insert_data_frame(session, contrast_table, Contrast.__table__)
    contrast_table = roger.util.as_data_frame(session.query(Contrast).filter(Contrast.DesignID == design_entry.ID))

    session.commit()
