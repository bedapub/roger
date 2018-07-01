from abc import ABC, abstractmethod

import pandas as pd
from pandas.compat import cStringIO
from biomart import BiomartServer


class AnnotationService(ABC):
    """Used to resolve probe sets, gene symbols and other gene-related identifiers to ROGER gene indices"""

    @abstractmethod
    def get_dataset(self, dataset_name):
        """Returns the dataset / context for the given dataset name"""
        return

    @abstractmethod
    def get_bulk_query_by_ds_name(self, dataset_name, params):
        """Performs bulk queries on a dataset based on the passed dataset name"""
        return

    @abstractmethod
    def get_bulk_query_by_ds(self, dataset, params):
        """Performs bulk queries on a given dataset / context object"""
        return


class RemoteEnsembleBioMartService(AnnotationService):
    """Performs all queries on remote Ensembl BioMart server"""

    def __init__(self):
        self.__server = BiomartServer("http://www.ensembl.org/biomart")

    def get_dataset(self, dataset_name):
        return self.__server.datasets[dataset_name]

    def get_bulk_query_by_ds_name(self, dataset_name, params):
        dataset = self.__server.datasets[dataset_name]
        response = dataset.search(params=params)
        result = pd.read_csv(cStringIO(response.text), sep='\t', names=params['attributes'])
        return result

    def get_bulk_query_by_ds(self, dataset, params):
        response = dataset.search(params=params)
        result = pd.read_csv(cStringIO(response.text), sep='\t', names=params['attributes'])
        return result


__annotation_service = RemoteEnsembleBioMartService()


def init_annotation_service(app):
    global __annotation_service
    annotation_service_type = "ENSEMBL"
    if 'ROGER_ANNOTATION_SERVICE' in app.config:
        annotation_service_type = app.config['ROGER_ANNOTATION_SERVICE']
    if annotation_service_type == 'ENSEMBL':
        __annotation_service = RemoteEnsembleBioMartService()
    else:
        raise RuntimeError("Unknown annotation service type: %s" % annotation_service_type)


def get_annotation_service() -> AnnotationService:
    return __annotation_service
