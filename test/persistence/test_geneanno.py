import unittest

from test import app
from test import db

import roger.logic.mart
import roger.persistence.geneanno

rat_dataset = "rnorvegicus_gene_ensembl"
rat_tax_id = 10116


class TestGeneAnnotationPersistence(unittest.TestCase):

    def test_list_species_and_import(self):
        with app.app_context():
            db.create_all()
            self.assertTrue(roger.persistence.geneanno.list_species(db.session()).empty)
            roger.persistence.geneanno.add_species(db.session(),
                                                   roger.persistence.geneanno.human_dataset,
                                                   roger.persistence.geneanno.human_tax_id)
            self.assertTrue(len(roger.persistence.geneanno.list_species(db.session())) == 1)
            self.assertTrue(len(db.session().query(roger.persistence.geneanno.Ortholog).limit(5).all()) > 0)
            roger.persistence.geneanno.add_species(db.session(), rat_dataset, rat_tax_id)
            self.assertTrue(len(roger.persistence.geneanno.list_species(db.session())) == 2)
            roger.persistence.geneanno.remove_species(db.session(), rat_tax_id)
            self.assertTrue(len(roger.persistence.geneanno.list_species(db.session())) == 1)
            db.drop_all()


if __name__ == '__main__':
    unittest.main()
