from pandas import read_sql, DataFrame
import getpass
import datetime
import os
import errno
from rpy2.robjects.packages import importr
from rpy2.robjects import conversion

base = importr("base")
ribios_io = importr("ribiosIO")


# TODO not transactional, each call to this method is atomic / includes commits
def insert_data_frame(session, df: DataFrame, table_name: str):
    df.to_sql(table_name, session.bind, if_exists='append', index=False)


def as_data_frame(query):
    return read_sql(query.statement, query.session.connection())


def get_current_datetime():
    return datetime.datetime.now()


# TODO not that reliable, consider real account management here
def get_current_user_name():
    return getpass.getuser()


# TODO replace dependency to ribiosIO in the future
def parse_gct(file_path):
    matrix = ribios_io.read_exprs_matrix(file_path)
    return DataFrame(conversion.ri2py(matrix),
                     columns=base.colnames(matrix),
                     index=base.rownames(matrix))


def silent_remove(filename):
    try:
        os.remove(filename)
    except OSError as e:  # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise e  # re-raise exception if a different error occurred
