from biomart import BiomartServer, BiomartDataset

from pandas import DataFrame, read_csv
from pandas.compat import cStringIO

from . import BioMartDataSet, AnnotationService

from roger.logic import cache
from roger.exception import ROGERUsageError


class RemoteBioMartDataSet(BioMartDataSet):

    def __init__(self, dataset: BiomartDataset):
        self.__dataset = dataset

    @property
    def attributes(self):
        col_names = ["name", "display_name"]
        return DataFrame([[getattr(i, j) for j in col_names] for i in self.__dataset.attributes.values()],
                         columns=col_names)

    @cache.memoize()
    def get_bulk_query(self, params):
        response = self.__dataset.search(params=params)
        result = read_csv(cStringIO(response.text), sep='\t', names=params['attributes'])
        return result

    @property
    def name(self):
        return self.__dataset.name

    @property
    def display_name(self):
        return self.__dataset.display_name


class RemoteEnsemblBioMartService(AnnotationService):
    """Performs all queries on remote Ensembl BioMart server"""

    def __init__(self):
        self.__server = BiomartServer("http://www.ensembl.org/biomart")

    def get_dataset(self, dataset_name):
        try:
            return RemoteBioMartDataSet(self.__server.datasets[dataset_name])
        except KeyError:
            raise ROGERUsageError("Dataset not found on Ensembl BioMart: %s" % dataset_name)
