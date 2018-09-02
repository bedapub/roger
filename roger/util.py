import getpass
import datetime
import os
import errno
import os.path

import numpy as np
import pandas as pd
from sqlalchemy import Table, func
from sqlalchemy.orm import Session

from roger.exception import ROGERUsageError


def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])


def read_df(file_path):
    return pd.read_table(file_path, sep="\t")


def write_df(df: pd.DataFrame, file_path):
    df.to_csv(file_path, sep="\t", index=False)


def get_next_free_db_id(session: Session, id_col):
    # VERY IMPORTANT: Never start indexing from 0 when having auto increment
    return session.query(func.coalesce(func.max(id_col), 0)).scalar() + 1


def insert_data(frame: pd.DataFrame):
    temp = frame
    column_names = list(map(str, temp.columns))

    data_list = [np.array(frame[col_name].get_values(), dtype=object) for col_name in frame.columns]
    return column_names, data_list


def insert_data_frame(session: Session, frame: pd.DataFrame, table: Table, chunk_size=None):
    frame_without_nans = frame.where((pd.notnull(frame)), None)
    keys, data_list = insert_data(frame_without_nans)

    nrows = len(frame_without_nans)

    if nrows == 0:
        return

    if chunk_size is None:
        chunk_size = nrows
    if chunk_size <= 0:
        raise ValueError('chunk_size argument should be a non-zero positive number')

    chunks = int(nrows / chunk_size) + 1

    for i in range(chunks):
        start_i = i * chunk_size
        end_i = min((i + 1) * chunk_size, nrows)
        if start_i >= end_i:
            break

        chunk_iter = zip(*[arr[start_i:end_i] for arr in data_list])
        data = [{k: v for k, v in zip(keys, row)} for row in chunk_iter]
        session.execute(table.insert(), data)


def as_data_frame(query):
    return pd.read_sql(query.statement, query.session.connection())


def get_current_datetime():
    return datetime.datetime.now()


# TODO not that reliable, consider real account management here
def get_current_user_name():
    return getpass.getuser()


def parse_gct(file_path):
    with open(file_path) as myfile:
        header = [next(myfile).rstrip() for _ in range(3)]

    version_line = header[0]
    dim_line = header[1].split("\t")
    col_line = header[2].split("\t")

    if version_line != "#1.2":
        raise ROGERUsageError("Unable to parse GCT file '%s': missing GCT header" % file_path)

    # Number of genes + number of samples
    n_dim_elems = 2

    if len(dim_line) != n_dim_elems:
        raise ROGERUsageError("Unable to parse GCT file '%s': missing dimension header in GCT header" % file_path)

    try:
        dims = [int(x) for x in header[1].split("\t")]
    except ValueError:
        raise ROGERUsageError("Unable to parse GCT file '%s': ill-formatted dimension header '%s'" %
                              (file_path, header[1]))

    # Name col + Description col + at least one sample col
    n_minimum_cols = 3

    if len(col_line) < n_minimum_cols or col_line[0].lower() != "name" or col_line[1].lower() != "description":
        raise ROGERUsageError("Unable to parse GCT file '%s': ill-formatted column header '%s ...'" %
                              (file_path, header[2][0:100]))

    sample_names = col_line[2:]

    if len(sample_names) != len(set(sample_names)):
        raise ROGERUsageError("Unable to parse GCT file '%s': duplicated sample names" % file_path)

    df = pd.read_table(file_path, sep="\t", skiprows=2, index_col=0)
    df = df.drop(columns=df.columns[0])
    df.index = df.index.astype(str)

    if dims[0] != df.shape[0]:
        raise ROGERUsageError("Unable to parse GCT file '%s': Number of expected genes don't match (%d vs %d)" %
                              (file_path, dims[0], df.shape[0]))

    if dims[1] != df.shape[1]:
        raise ROGERUsageError("Unable to parse GCT file '%s': Number of expected samples don't match (%d vs %d)" %
                              (file_path, dims[1], df.shape[1]))

    if any([col_type.name == "object" for col_type in df.dtypes]):
        raise ROGERUsageError("Uable to parse GCT file '%s': counts / signal columns have non-numeric values" %
                              file_path)

    gene_duplicates = df.index.duplicated()
    if any(gene_duplicates):
        raise ROGERUsageError("Unable to parse GCT file '%s': duplicated row names '%s ...'" %
                              (file_path, df[gene_duplicates].index[0:2].tolist()))

    return df


def silent_rmdir(dir_path):
    if dir_path is None:
        return
    try:
        os.rmdir(dir_path)
    except OSError as e:
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise e  # re-raise exception if a different error occurred


def silent_remove(filename):
    if filename is None:
        return
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise e  # re-raise exception if a different error occurred


def abspath_or_none(file):
    if file is None:
        return None
    return os.path.abspath(file)
