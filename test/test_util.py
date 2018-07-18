import unittest
import pandas as pd

from test import app
from test import db
from roger.persistence.schema import GeneAnnotation
import roger.util


class TestUtil(unittest.TestCase):

    def test_insert_data_frame(self):
        with app.app_context():
            db.create_all()
            session = db.session()
            df = pd.read_table("../test_data/annotation/example_insert.csv", sep=",")

            genes = pd.DataFrame({'Version': "test",
                                  'TaxID': 1234,
                                  'EnsemblGeneID': df["ensembl_gene_id"],
                                  'EntrezGeneID': df["entrezgene"].apply(roger.util.nan_to_none),
                                  'GeneType': df["gene_biotype"],
                                  'GeneSymbol': df["external_gene_name"],
                                  'IsObsolete': False})

            roger.util.insert_data_frame(session, genes, GeneAnnotation.__table__)
            session.commit()
            self.assertTrue(len(db.session().query(GeneAnnotation).all()) > 1)
            db.drop_all()


if __name__ == '__main__':
    unittest.main()
