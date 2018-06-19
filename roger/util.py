import pandas as pd


def as_data_frame(query):
    return pd.read_sql(query.statement, query.session.connection())
