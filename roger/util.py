import getpass
import datetime
import os
import errno
import numpy as np
import pandas as pd
from sqlalchemy import Table, func
from sqlalchemy.orm import Session

from enum import EnumMeta


def read_df(file_path):
    return pd.read_table(file_path, sep="\t")


def write_df(df: pd.DataFrame, file_path):
    df.to_csv(file_path, sep="\t", index=False)


def get_or_guess_name(name, source_file=None):
    if name is None and source_file is not None:
        return os.path.splitext(os.path.basename(source_file))[0]
    return name


def get_enum_names(enum: EnumMeta):
    return [e.name for e in list(enum)]


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
    df = pd.read_csv(file_path, sep="\t", skiprows=2, index_col=0)
    return df.drop(columns=df.columns[0])


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
