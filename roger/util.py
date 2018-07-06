from pandas import read_sql, DataFrame
import getpass
import datetime


# TODO not transactional, each call to this method is atomic / includes commits
def insert_data_frame(session, df: DataFrame, table_name : str):
    df.to_sql(table_name, session.bind, if_exists='append', index=False)


def as_data_frame(query):
    return read_sql(query.statement, query.session.connection())


def get_current_datetime():
    return datetime.datetime.now()


# TODO not that reliable, consider real account management here
def get_current_user_name():
    return getpass.getuser()
