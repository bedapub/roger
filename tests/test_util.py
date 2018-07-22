import pandas as pd

from tests import app
from tests import db
from roger.persistence.schema import GeneAnnotation
import roger.util


def test_insert_data_frame():
    with app.app_context():
        db.create_all()
        session = db.session()
        df = pd.read_table("test_data/annotation/rat_geneanno_92.csv", sep=",")

        genes = pd.DataFrame({'Version': "tests",
                              'TaxID': 1234,
                              'EnsemblGeneID': df["ensembl_gene_id"],
                              'EntrezGeneID': df["entrezgene"].apply(roger.util.nan_to_none),
                              'GeneType': df["gene_biotype"],
                              'GeneSymbol': df["external_gene_name"],
                              'IsObsolete': False})

        roger.util.insert_data_frame(session, genes, GeneAnnotation.__table__)
        session.commit()
        assert len(db.session().query(GeneAnnotation).all()) > 1
        db.drop_all()


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
    assert all([a == b for a, b in zip(parsed.columns, exp_cols)])
