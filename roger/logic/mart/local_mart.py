from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from rpy2 import robjects

from . import BioMartDataSet, AnnotationService

ribiosBioMart = importr("ribiosBioMart")
DBI = importr("DBI")
RMySQL = importr("RMySQL")
base = importr("base")


class LocalBioMartDataSet(BioMartDataSet):

    def __init__(self, dataset, name):
        self.__dataset = dataset
        self.__name = name

    @property
    def attributes(self):
        return pandas2ri.ri2py(ribiosBioMart.listLocalAttributes(self.__dataset))

    def get_bulk_query(self, params):
        filters = robjects.r("NULL")
        if "filters" in params:
            filters = robjects.vectors.ListVector(params["filters"])
        response = ribiosBioMart.getLocalBM(mart=self.__dataset,
                                            attributes=params["attributes"],
                                            filters=filters)
        return pandas2ri.ri2py(response)

    @property
    def name(self):
        return self.__name

    @property
    def display_name(self):
        return self.__dataset.name


# TODO: Potential resource leak due to not cleaning up SQL connection
class LocalEnsemblBioMartService(AnnotationService):
    """Performs all queries on remote Ensembl BioMart server"""

    def __init__(self, db_host, db_port, db_name, db_username, db_password):
        self.__db_host = db_host
        self.__db_port = db_port
        self.__db_name = db_name
        self.__db_username = db_username
        self.__db_password = db_password

    def get_dataset(self, dataset_name):
        con = DBI.dbConnect(RMySQL.MySQL(),
                            host=self.__db_host,
                            port=self.__db_port,
                            dbname=self.__db_name,
                            user=self.__db_username,
                            password=self.__db_password)
        return LocalBioMartDataSet(ribiosBioMart.useLocalMart(con, dataset_name), dataset_name)
