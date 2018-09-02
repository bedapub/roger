import pytest
from flask_sqlalchemy import SQLAlchemy
from pandas import DataFrame
from pandas.util.testing import assert_frame_equal

from roger.logic.util.exception import ROGERUsageError
from roger.logic.dge import annotate_ds_pheno_data
from roger.persistence.dge import check_design_matrix, get_contrast
from roger.logic.util.data import parse_gct
from tests import has_equal_elements


class TestCheckMatrices(object):
    def test_check_matrix(self):
        exprs_data = parse_gct("test_data/ds/dummy/small.gct")

        design_matrix = DataFrame()
        design_matrix['Group1'] = [1, 1, 1]
        design_matrix['Group2'] = [0, 1, 0]
        design_matrix['Group3'] = [0, 0, 1]

        check_design_matrix(exprs_data.columns, design_matrix)

        design_matrix = DataFrame(index=["A", "B", "C"])
        design_matrix['Group1'] = [1, 1, 1]
        design_matrix['Group2'] = [0, 1, 0]
        design_matrix['Group3'] = [0, 0, 1]

        check_design_matrix(exprs_data.columns, design_matrix)

    def test_check_matrix_fail_on_row_count_mismatch(self):
        exprs_data = parse_gct("test_data/ds/dummy/small.gct")

        design_matrix = DataFrame()
        design_matrix['Group1'] = [1, 1]
        design_matrix['Group2'] = [0, 1]
        design_matrix['Group3'] = [0, 0]

        with pytest.raises(ROGERUsageError):
            check_design_matrix(exprs_data.columns, design_matrix)

    def test_check_matrix_fail_on_index_mismatch(self):
        exprs_data = parse_gct("test_data/ds/dummy/small.gct")

        design_matrix = DataFrame(index=["A", "B", "D"])
        design_matrix['Group1'] = [1, 1, 1]
        design_matrix['Group2'] = [0, 1, 0]
        design_matrix['Group3'] = [0, 0, 1]

        with pytest.raises(ROGERUsageError):
            check_design_matrix(exprs_data.columns, design_matrix)

    def test_check_matrix_fail_on_noh_integer_data(self):
        exprs_data = parse_gct("test_data/ds/dummy/small.gct")

        design_matrix = DataFrame(index=["A", "B", "C"])
        design_matrix['Group1'] = [1, 1, 1]
        design_matrix['Group2'] = [0, "A", 0]
        design_matrix['Group3'] = [0, 0, 1]

        with pytest.raises(ROGERUsageError):
            check_design_matrix(exprs_data.columns, design_matrix)


class TestPhenoAnnotation(object):
    def test_annotate_pheno_with_no_pheno(self):
        expected_df = DataFrame()
        expected_df['SAMPLE'] = ["A", "B", "C"]

        exprs_data = parse_gct("test_data/ds/dummy/small.gct")
        annotated_pheno = annotate_ds_pheno_data(exprs_data)
        assert_frame_equal(annotated_pheno, expected_df)

    def test_annotate_pheno_witn_simple_pheno(self):
        pheno_df = DataFrame()
        pheno_df['CellType'] = ["Microglia", "Macrophage", "Macrophage"]
        pheno_df['Donor'] = ["Donor A", "Donor A", "Donor A"]

        expected_df = DataFrame()
        expected_df['SAMPLE'] = ["A", "B", "C"]
        expected_df['CellType'] = ["Microglia", "Macrophage", "Macrophage"]
        expected_df['Donor'] = ["Donor A", "Donor A", "Donor A"]

        exprs_data = parse_gct("test_data/ds/dummy/small.gct")
        annotated_pheno = annotate_ds_pheno_data(exprs_data, pheno_df)
        assert_frame_equal(annotated_pheno, expected_df)

    def test_annotate_pheno_mismatching_counts(self):
        pheno_df = DataFrame()
        pheno_df['CellType'] = ["Microglia", "Macrophage"]
        pheno_df['Donor'] = ["Donor A", "Donor A"]

        exprs_data = parse_gct("test_data/ds/dummy/small.gct")
        with pytest.raises(ROGERUsageError):
            annotate_ds_pheno_data(exprs_data, pheno_df)

    def test_annotate_pheno_witn_pheno_and_sample_col(self):
        pheno_df = DataFrame()
        pheno_df['CellType'] = ["Microglia", "Macrophage", "Macrophage"]
        pheno_df['Donor'] = ["Donor A", "Donor A", "Donor A"]
        pheno_df['SAMPLE'] = ["C", "A", "B"]

        expected_df = DataFrame()
        expected_df['CellType'] = ["Microglia", "Macrophage", "Macrophage"]
        expected_df['Donor'] = ["Donor A", "Donor A", "Donor A"]
        expected_df['SAMPLE'] = ["C", "A", "B"]

        exprs_data = parse_gct("test_data/ds/dummy/small.gct")
        annotated_pheno = annotate_ds_pheno_data(exprs_data, pheno_df)
        assert_frame_equal(annotated_pheno, expected_df)

    def test_annotate_pheno_with_mismatching_sample_names(self):
        pheno_df = DataFrame()
        pheno_df['CellType'] = ["Microglia", "Macrophage", "Macrophage"]
        pheno_df['Donor'] = ["Donor A", "Donor A", "Donor A"]
        pheno_df['SAMPLE'] = ["C", "A", "D"]

        exprs_data = parse_gct("test_data/ds/dummy/small.gct")
        with pytest.raises(ROGERUsageError):
            annotate_ds_pheno_data(exprs_data, pheno_df)


class TestDataSet(object):
    def test_feature_data(self, sqlite_datasets: SQLAlchemy):
        session = sqlite_datasets.session()

        contrast_data = get_contrast(session,
                                     "rnaseq-example-ContrastMatrix",
                                     "rnaseq-example-DesignMatrix",
                                     "rnaseq-example-readCounts")
        design_data = contrast_data.Design
        ds_data = design_data.DataSet

        assert has_equal_elements(ds_data.exprs_data.index, ds_data.feature_data.Name)
