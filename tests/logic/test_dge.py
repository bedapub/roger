import pytest
from flask_sqlalchemy import SQLAlchemy
from pandas import read_table

from roger.logic.dge import perform_edger, perform_limma
from roger.persistence.dge import get_contrast
from roger.util import read_df
from tests import has_equal_elements


class TestDGEAnalysis(object):
    @pytest.mark.parametrize("algorithm, contrast_name, design_name, ds_name, expected_dge_file, feature_subset", [
        (perform_limma,
         "ma-example-contrast",
         "ma-example-design",
         "ma-example-signals",
         "test_data/ds/ma-example-dgeTable.txt",
         "test_data/ds/ma-example-featureSubset.txt"),
        (perform_edger,
         "rnaseq-example-ContrastMatrix",
         "rnaseq-example-DesignMatrix",
         "rnaseq-example-readCounts",
         "test_data/ds/rnaseq-example-dgeTable.txt",
         "test_data/ds/rnaseq-example-featureSubset.txt")
    ])
    def test_dge_algos(self, algorithm, contrast_name, design_name, ds_name, expected_dge_file, feature_subset,
                       sqlite_datasets: SQLAlchemy):
        session = sqlite_datasets.session()

        contrast_data = get_contrast(session,
                                     contrast_name,
                                     design_name,
                                     ds_name)

        design_data = contrast_data.Design
        ds_data = design_data.DataSet

        eset, eset_fit, dge_tbl, subset = algorithm(ds_data.ExprsWC,
                                                    ds_data.feature_data,
                                                    design_data.design_matrix,
                                                    contrast_data.contrast_matrix)

        expected_dge = read_df(expected_dge_file)

        # TODO: We cannot simply compare the entire frame, since gene annotation comes from
        # a external Ensembl installation and that can change over time
        # Alternative: Use Mocked instance of annotation service
        assert has_equal_elements(dge_tbl["Contrast"], expected_dge["Contrast"])
        assert has_equal_elements(dge_tbl["FeatureIndex"], expected_dge["FeatureIndex"])
        assert has_equal_elements(dge_tbl["Name"], expected_dge["Name"])
        assert has_equal_elements(dge_tbl["logFC"], expected_dge["logFC"], epsilon=0.0001)
        assert has_equal_elements(dge_tbl["AveExpr"], expected_dge["AveExpr"], epsilon=0.0001)
        assert has_equal_elements(dge_tbl["t"], expected_dge["t"], epsilon=0.0001)
        assert has_equal_elements(dge_tbl["PValue"], expected_dge["PValue"], epsilon=0.0001)
        assert has_equal_elements(dge_tbl["FDR"], expected_dge["FDR"], epsilon=0.0001)

        assert has_equal_elements(subset, read_table(feature_subset, header=None).ix[:, 0])
