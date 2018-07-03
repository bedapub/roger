from pandas import read_sql
import getpass
import datetime


def as_data_frame(query):
    return read_sql(query.statement, query.session.connection())


def get_current_datetime():
    return datetime.datetime.now()


# TODO not that reliable, consider real account management here
def get_current_user_name():
    return getpass.getuser()

