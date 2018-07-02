from abc import ABC, abstractmethod

import pandas as pd
from pandas.compat import cStringIO
from biomart import BiomartServer, BiomartDataset
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from rpy2 import robjects


class BioMartDataSet(ABC):

    def __repr__(self):
        return "%s(name=%s)" % (self.__class__.__name__, self.name)

    @property
    @abstractmethod
    def attributes(self):
        """Returns all available attributes as :func:pandas.DataFrame"""
        return

    @abstractmethod
    def get_bulk_query(self, params):
        """Performs bulk queries on a given dataset / context object"""
        return

    @property
    @abstractmethod
    def name(self):
        return

    @property
    @abstractmethod
    def display_name(self):
        return

    # TODO enable this for automatic symbol discovery
    # def query_biomart_symbols(self, samples, attr_candidate):
    #    return self.get_bulk_query({
    #        "attributes": [attr_candidate, "ensembl_gene_id"],
    #        "filters": {
    #            attr_candidate: samples
    #        }
    #    })

    # def discover_best_attribute(self, dataset, sample, attr_candidates):
    #    responses = [(attr_candidate, self.query_biomart_symbols(dataset, sample, attr_candidate))
    #                 for attr_candidate in attr_candidates]
    #
    #    match_counts = [(attr_candidate, df.shape[0]) for (attr_candidate, df) in responses]
    #    max_matches = max([matches for (attr, matches) in match_counts])
    #    for (attr, matches) in reversed(match_counts):
    #        if matches == max_matches:
    #            return attr
    #
    #    raise RuntimeError("Unable to find matching BioMart attribute")


class RemoteBioMartDataSet(BioMartDataSet):

    def __init__(self, dataset: BiomartDataset):
        self.__dataset = dataset

    @property
    def attributes(self):
        col_names = ["name", "display_name"]
        return pd.DataFrame([[getattr(i, j) for j in col_names] for i in self.__dataset.attributes.values()],
                            columns=col_names)

    def get_bulk_query(self, params):
        response = self.__dataset.search(params=params)
        result = pd.read_csv(cStringIO(response.text), sep='\t', names=params['attributes'])
        return result

    @property
    def name(self):
        return self.__dataset.name

    @property
    def display_name(self):
        return self.__dataset.display_name


class LocalBioMartDataSet(BioMartDataSet):

    def __init__(self, ribios_bio_mart_pkg, dataset, name):
        self.__ribiosBioMart = ribios_bio_mart_pkg
        self.__dataset = dataset
        self.__name = name

    @property
    def attributes(self):
        return pandas2ri.ri2py(self.__ribiosBioMart.listLocalAttributes(self.__dataset))

    def get_bulk_query(self, params):
        filters = robjects.r("NULL")
        if "filters" in params:
            filters = robjects.vectors.ListVector(params["filters"])
        response = self.__ribiosBioMart.getLocalBM(mart=self.__dataset,
                                                   attributes=params["attributes"],
                                                   filters=filters)
        return pandas2ri.ri2py(response)

    @property
    def name(self):
        return self.__name

    @property
    def display_name(self):
        return self.__dataset.name


class AnnotationService(ABC):
    """Used to resolve probe sets, gene symbols and other gene-related identifiers to ROGER gene indices"""

    def __repr__(self):
        return self.__class__.__name__

    @abstractmethod
    def get_dataset(self, dataset_name) -> BioMartDataSet:
        """Returns the dataset / context for the given dataset name"""
        return BioMartDataSet()

    def get_bulk_query(self, dataset_name, params):
        """Performs bulk queries on a dataset based on the passed dataset name"""
        return self.get_dataset(dataset_name).get_bulk_query(params)


class RemoteEnsemblBioMartService(AnnotationService):
    """Performs all queries on remote Ensembl BioMart server"""

    def __init__(self):
        self.__server = BiomartServer("http://www.ensembl.org/biomart")

    def get_dataset(self, dataset_name):
        return RemoteBioMartDataSet(self.__server.datasets[dataset_name])


# TODO: Potential resource leak due to
class LocalEnsemblBioMartService(AnnotationService):
    """Performs all queries on remote Ensembl BioMart server"""

    def __init__(self, db_host, db_port, db_name, db_username, db_password):
        self.__db_host = db_host
        self.__db_port = db_port
        self.__db_name = db_name
        self.__db_username = db_username
        self.__db_password = db_password
        self.__ribiosBioMart = importr("ribiosBioMart")
        self.__DBI = importr("DBI")
        self.__RMySQL = importr("RMySQL")
        self.__base = importr("base")

    def get_dataset(self, dataset_name):
        con = self.__DBI.dbConnect(self.__RMySQL.MySQL(),
                                   host=self.__db_host,
                                   port=self.__db_port,
                                   dbname=self.__db_name,
                                   user=self.__db_username,
                                   password=self.__db_password)
        return LocalBioMartDataSet(self.__ribiosBioMart,
                                   self.__ribiosBioMart.useLocalMart(con, dataset_name),
                                   dataset_name)


# TODO move this to the global flask application context (http://flask.pocoo.org/docs/1.0/appcontext)
__annotation_service = RemoteEnsemblBioMartService()


def init_annotation_service(app):
    global __annotation_service
    annotation_service_type = "ENSEMBL"
    if 'ROGER_ANNOTATION_SERVICE' in app.config:
        annotation_service_type = app.config['ROGER_ANNOTATION_SERVICE']
    if annotation_service_type == 'ENSEMBL':
        __annotation_service = RemoteEnsemblBioMartService()
    elif annotation_service_type == 'LOCAL':
        __annotation_service = LocalEnsemblBioMartService(
            app.config.get('ROGER_ANNOTATION_DBHOST', None),
            app.config.get('ROGER_ANNOTATION_DBPORT', None),
            app.config.get('ROGER_ANNOTATION_DBUSER', None),
            app.config.get('ROGER_ANNOTATION_DBPASSWD', None),
            app.config.get('ROGER_ANNOTATION_DB', None)
        )
    else:
        raise RuntimeError("Unknown annotation service type: %s" % annotation_service_type)


def get_annotation_service() -> AnnotationService:
    return __annotation_service
