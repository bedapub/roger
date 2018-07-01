from pandas import read_sql


def as_data_frame(query):
    return read_sql(query.statement, query.session.connection())
