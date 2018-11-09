from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.engine.base import Engine
from sqlite3 import Connection as SQLite3Connection

from flask_sqlalchemy import SQLAlchemy

__use_foreign_keys = True


@contextmanager
def disabled_foreign_keys():
    global __use_foreign_keys
    __use_foreign_keys = False
    yield
    __use_foreign_keys = True


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    del connection_record
    if isinstance(dbapi_connection, SQLite3Connection) and __use_foreign_keys:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


db = SQLAlchemy()
