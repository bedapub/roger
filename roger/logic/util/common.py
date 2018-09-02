import os
from enum import EnumMeta


def get_enum_names(enum: EnumMeta):
    return [e.name for e in list(enum)]


def get_or_guess_name(name, source_file=None):
    if name is None and source_file is not None:
        return os.path.splitext(os.path.basename(source_file))[0]
    return name
