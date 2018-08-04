import pytest
from flask_sqlalchemy import SQLAlchemy
from roger.logic.dge import perform_edger, perform_limma

import roger.logic
import roger.logic.mart
import roger.logic.geneanno
import roger.persistence.geneanno
import roger.persistence.dge
from roger.util import read_df
from tests import has_equal_elements


class TestDataSet(object):
    def test_feature_data(self, sqlite_datasets: SQLAlchemy):
        session = sqlite_datasets.session()

        contrast_data = roger.persistence.dge.get_contrast(session,
                                                           "rnaseq-example-ContrastMatrix",
                                                           "rnaseq-example-DesignMatrix",
                                                           "rnaseq-example-readCounts")
        design_data = contrast_data.Design
        ds_data = design_data.DataSet

        assert has_equal_elements(ds_data.exprs_data.index, ds_data.feature_data.Name)


class TestDGEAnalysis(object):
    @pytest.mark.parametrize("algorithm, contrast_name, design_name, ds_name, expected_dge_file", [
        (perform_limma,
         "ma-example-contrast",
         "ma-example-design",
         "ma-example-signals",
         "test_data/ds/ma-example-dgeTable.txt"),
        (perform_edger,
         "rnaseq-example-ContrastMatrix",
         "rnaseq-example-DesignMatrix",
         "rnaseq-example-readCounts",
         "test_data/ds/rnaseq-example-dgeTable.txt")
    ])
    def test_dge_algos(self, algorithm, contrast_name, design_name, ds_name, expected_dge_file,
                       sqlite_datasets: SQLAlchemy):
        session = sqlite_datasets.session()

        contrast_data = roger.persistence.dge.get_contrast(session,
                                                           contrast_name,
                                                           design_name,
                                                           ds_name)

        design_data = contrast_data.Design
        ds_data = design_data.DataSet

        eset, eset_fit, dge_tbl, used_feature_names = algorithm(ds_data.ExprsWC,
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
