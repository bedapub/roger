import pytest
from flask_sqlalchemy import SQLAlchemy
from pandas import read_table, DataFrame
from pandas.util.testing import assert_frame_equal

from roger.exception import ROGERUsageError
from roger.logic.dge import perform_edger, perform_limma, annotate_ds_pheno_data

import roger.logic
import roger.logic.mart
import roger.logic.geneanno
import roger.persistence.geneanno
import roger.persistence.dge
from roger.util import read_df, parse_gct
from tests import has_equal_elements


class TestCheckMatrices(object):
    def test_check_matrix(self):
        exprs_data = parse_gct("test_data/ds/dummy/small.gct")

        design_matrix = DataFrame()
        design_matrix['Group1'] = [1, 1, 1]
        design_matrix['Group2'] = [0, 1, 0]
        design_matrix['Group3'] = [0, 0, 1]

        roger.persistence.dge.check_design_matrix(exprs_data.columns, design_matrix)

        design_matrix = DataFrame(index=["A", "B", "C"])
        design_matrix['Group1'] = [1, 1, 1]
        design_matrix['Group2'] = [0, 1, 0]
        design_matrix['Group3'] = [0, 0, 1]

        roger.persistence.dge.check_design_matrix(exprs_data.columns, design_matrix)

    def test_check_matrix_fail_on_row_count_mismatch(self):
        exprs_data = parse_gct("test_data/ds/dummy/small.gct")

        design_matrix = DataFrame()
        design_matrix['Group1'] = [1, 1]
        design_matrix['Group2'] = [0, 1]
        design_matrix['Group3'] = [0, 0]

        with pytest.raises(ROGERUsageError):
            roger.persistence.dge.check_design_matrix(exprs_data.columns, design_matrix)

    def test_check_matrix_fail_on_index_mismatch(self):
        exprs_data = parse_gct("test_data/ds/dummy/small.gct")

        design_matrix = DataFrame(index=["A", "B", "D"])
        design_matrix['Group1'] = [1, 1, 1]
        design_matrix['Group2'] = [0, 1, 0]
        design_matrix['Group3'] = [0, 0, 1]

        with pytest.raises(ROGERUsageError):
            roger.persistence.dge.check_design_matrix(exprs_data.columns, design_matrix)

    def test_check_matrix_fail_on_noh_integer_data(self):
        exprs_data = parse_gct("test_data/ds/dummy/small.gct")

        design_matrix = DataFrame(index=["A", "B", "C"])
        design_matrix['Group1'] = [1, 1, 1]
        design_matrix['Group2'] = [0, "A", 0]
        design_matrix['Group3'] = [0, 0, 1]

        with pytest.raises(ROGERUsageError):
            roger.persistence.dge.check_design_matrix(exprs_data.columns, design_matrix)


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

        contrast_data = roger.persistence.dge.get_contrast(session,
                                                           "rnaseq-example-ContrastMatrix",
                                                           "rnaseq-example-DesignMatrix",
                                                           "rnaseq-example-readCounts")
        design_data = contrast_data.Design
        ds_data = design_data.DataSet

        assert has_equal_elements(ds_data.exprs_data.index, ds_data.feature_data.Name)


class TestDGEAnalysis(object):
    @pytest.mark.skip("TODO")
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

        contrast_data = roger.persistence.dge.get_contrast(session,
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
