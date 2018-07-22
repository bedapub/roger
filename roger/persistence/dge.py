import os.path

from roger.persistence.schema import DGEmethod, DataSet
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
