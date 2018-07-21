import getpass
import datetime
import os
import errno
from cmapPy.pandasGEXpress.parse import parse as cmap_parse
import numpy as np
import pandas as pd
from sqlalchemy import Table, func
from sqlalchemy.orm import Session


def get_next_free_db_id(session: Session, id_col):
    return session.query(func.coalesce(func.max(id_col), -1)).scalar() + 1


def nan_to_none(val):
    import math
    if math.isnan(val):
        return None
    return val


def insert_data(frame: pd.DataFrame):
    temp = frame
    column_names = list(map(str, temp.columns))

    data_list = [np.array(frame[col_name].get_values(), dtype=object) for col_name in frame.columns]
    return column_names, data_list

    #ncols = len(column_names)
    #data_list = [None] * ncols
    #blocks = temp._data.blocks
    #for i in range(len(blocks)):
    #    b = blocks[i]
    #    if b.is_datetime:
    #        # convert to microsecond resolution so this yields
    #        # datetime.datetime
    #        d = b.values.astype('M8[us]').astype(object)
    #    else:
    #        d = np.array(b.get_values(), dtype=object)
    #
    #    for col_loc, col in zip(b.mgr_locs, d):
    #        data_list[col_loc] = col

    #print(data_list)
    #return column_names, data_list


def insert_data_frame(session: Session, frame: pd.DataFrame, table: Table, chunk_size=None):
    keys, data_list = insert_data(frame)

    nrows = len(frame)

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


# TODO replace dependency to ribiosIO in the future
def parse_gct(file_path):
    return cmap_parse(file_path).data_df


def silent_remove(filename):
    try:
        os.remove(filename)
    except OSError as e:  # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise e  # re-raise exception if a different error occurred
