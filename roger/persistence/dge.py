from roger.persistence.schema import DGEmethod, DataSet
from roger.util import as_data_frame
from roger.exception import ROGERUsageError

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
        raise ROGERUsageError('DGE does not exist in database: %s' % name)

    session.query(DGEmethod).filter(DGEmethod.Name == name).delete()
    session.commit()

# --------------------------
# Data sets
# --------------------------


def list_datasets(session):
    return as_data_frame(session.query(DataSet))


def add_dataset(session, name, description, version):
    method = DataSet()
    session.add(method)
    session.commit()


def delete_dataset(session, name):
    # Check if DGE method is already preset in the database
    gse_methods = list_methods(session)
    if gse_methods[gse_methods.Name == name].empty:
        raise ROGERUsageError('DGE does not exist in database: %s' % name)

    session.query(DGEmethod).filter(DGEmethod.Name == name).delete()
    session.commit()
