import pandas as pd
import pytest

from roger.exception import ROGERUsageError
from roger.persistence.schema import GeneAnnotation

import roger.util
from tests import has_equal_elements


def test_insert_data_frame(sqlite_in_memory):
    session = sqlite_in_memory.session()
    df = pd.read_table("test_data/annotation/rat_geneanno_92.csv", sep=",")

    genes = pd.DataFrame({'Version': "tests",
                          'TaxID': 1234,
                          'EnsemblGeneID': df["ensembl_gene_id"],
                          'EntrezGeneID': df["entrezgene"],
                          'GeneType': df["gene_biotype"],
                          'GeneSymbol': df["external_gene_name"],
                          'IsObsolete': False})

    roger.util.insert_data_frame(session, genes, GeneAnnotation.__table__)
    session.commit()
    assert len(session.query(GeneAnnotation).all()) > 1


def test_parse_gct_file():
    parsed = roger.util.parse_gct("test_data/ds/ma-example-signals.gct")

    exp_cols = ['DS_10210_LNA_invivo_R13537_1', 'DS_10210_LNA_invivo_R13537_2',
                'DS_10210_LNA_invivo_R13537_3', 'DS_10210_LNA_invivo_R13537_4',
                'DS_10210_LNA_invivo_R13539_1', 'DS_10210_LNA_invivo_R13539_2',
                'DS_10210_LNA_invivo_R13539_3', 'DS_10210_LNA_invivo_R13539_4',
                'DS_10210_LNA_invivo_R13541_1', 'DS_10210_LNA_invivo_R13541_2',
                'DS_10210_LNA_invivo_R13541_3', 'DS_10210_LNA_invivo_R13541_4',
                'DS_10210_LNA_invivo_R13549_1', 'DS_10210_LNA_invivo_R13549_2',
                'DS_10210_LNA_invivo_R13549_3', 'DS_10210_LNA_invivo_R13549_4',
                'DS_10210_LNA_invivo_R13551_1', 'DS_10210_LNA_invivo_R13551_2',
                'DS_10210_LNA_invivo_R13551_3', 'DS_10210_LNA_invivo_R13551_4',
                'DS_10210_LNA_invivo_saline_1', 'DS_10210_LNA_invivo_saline_2',
                'DS_10210_LNA_invivo_saline_3', 'DS_10210_LNA_invivo_saline_4']

    assert parsed.shape == (45101, 24)
    assert "1415670_at" in parsed.index
    assert has_equal_elements(parsed.columns, exp_cols)


@pytest.mark.parametrize("test_file", [
    "test_data/ds/wrong_gct/no_header.gct",
    "test_data/ds/wrong_gct/no_dim_header.gct",
    "test_data/ds/wrong_gct/gene_mismatch.gct",
    "test_data/ds/wrong_gct/sample_mismatch.gct",
    "test_data/ds/wrong_gct/duplicated_cols.gct",
    "test_data/ds/wrong_gct/duplicated_genes.gct"
])
def test_parse_broken_gct_files(test_file):
    with pytest.raises(ROGERUsageError):
        roger.util.parse_gct(test_file)
