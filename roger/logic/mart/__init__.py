from abc import ABC, abstractmethod


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
