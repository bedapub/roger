from sqlalchemy import event
from sqlalchemy.engine.base import Engine
from sqlite3 import Connection as SQLite3Connection


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    del connection_record
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
