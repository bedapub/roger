import datetime
import errno
import getpass
import os
from enum import EnumMeta


def get_enum_names(enum: EnumMeta):
    return [e.name for e in list(enum)]


def get_or_guess_name(name, source_file=None):
    if name is None and source_file is not None:
        return os.path.splitext(os.path.basename(source_file))[0]
    return name


def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])


def get_current_datetime():
    return datetime.datetime.now()


# TODO not that reliable, consider real account management here
def get_current_user_name():
    return getpass.getuser()


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


def merge_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z
