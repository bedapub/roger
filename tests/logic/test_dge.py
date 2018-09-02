import pytest
from flask_sqlalchemy import SQLAlchemy
from pandas import read_table

from roger.logic.dge import DGEAlgorithm, LimmaDGE, EdgeRDGE, init_methods
from roger.persistence.dge import get_contrast, list_methods
from roger.logic.util.data import read_df
from tests import has_equal_elements


class TestDGEMethodInit(object):
    def test_dge_methods_exist_on_init(self, sqlite_in_memory):
        session = sqlite_in_memory.session()
        init_methods(session)
        assert len(list_methods(session)) > 1


class TestDGEAnalysis(object):
    @pytest.mark.parametrize("algorithm, contrast_name, design_name, ds_name, expected_dge_file, feature_subset", [
        (LimmaDGE(),
         "ma-example-contrast",
         "ma-example-design",
         "ma-example-signals",
         "test_data/ds/ma-example-dgeTable.txt",
         "test_data/ds/ma-example-featureSubset.txt"),
        (EdgeRDGE(),
         "rnaseq-example-ContrastMatrix",
         "rnaseq-example-DesignMatrix",
         "rnaseq-example-readCounts",
         "test_data/ds/rnaseq-example-dgeTable.txt",
         "test_data/ds/rnaseq-example-featureSubset.txt")
    ])
    def test_dge_algos(self, algorithm: DGEAlgorithm,
                       contrast_name,
                       design_name,
                       ds_name,
                       expected_dge_file,
                       feature_subset,
                       sqlite_datasets: SQLAlchemy):
        session = sqlite_datasets.session()

        contrast_data = get_contrast(session,
                                     contrast_name,
                                     design_name,
                                     ds_name)

        design_data = contrast_data.Design
        ds_data = design_data.DataSet

        dge_result = algorithm.exec_dge(ds_data.ExprsWC,
                                        ds_data.feature_data,
                                        design_data,
                                        contrast_data.contrast_matrix)

        expected_dge = read_df(expected_dge_file)

        # TODO: We cannot simply compare the entire frame, since gene annotation comes from
        # an external Ensembl installation and that can change over time
        # Alternative: Use Mocked instance of annotation service
        assert has_equal_elements(dge_result.dge_table["Contrast"], expected_dge["Contrast"])
        assert has_equal_elements(dge_result.dge_table["FeatureIndex"], expected_dge["FeatureIndex"])
        assert has_equal_elements(dge_result.dge_table["Name"], expected_dge["Name"])
        assert has_equal_elements(dge_result.dge_table["logFC"], expected_dge["logFC"], epsilon=0.0001)
        assert has_equal_elements(dge_result.dge_table["AveExpr"], expected_dge["AveExpr"], epsilon=0.0001)
        assert has_equal_elements(dge_result.dge_table["t"], expected_dge["t"], epsilon=0.0001)
        assert has_equal_elements(dge_result.dge_table["PValue"], expected_dge["PValue"], epsilon=0.0001)
        assert has_equal_elements(dge_result.dge_table["FDR"], expected_dge["FDR"], epsilon=0.0001)

        assert has_equal_elements(dge_result.used_feature_list, read_table(feature_subset, header=None).ix[:, 0])
