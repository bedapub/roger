import enum


class ExprsType(enum.Enum):
    MICRO_ARRAY = 1
    RNA_SEQ = 2


class MicroArrayType(enum.Enum):
    RMA = 1
    MAS5 = 2


class RNASeqType(enum.Enum):
    RPKMS = 1
