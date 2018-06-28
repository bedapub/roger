import unittest
from flask import Flask

from roger.main import db
import roger.backend.geneanno

app = Flask('roger_test')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

rat_dataset = "rnorvegicus_gene_ensembl"
rat_tax_id = 10116


class TestGeneAnnotationPersistence(unittest.TestCase):

    def test_list_species_and_import(self):
        with app.app_context():
            db.create_all()
            self.assertTrue(roger.backend.geneanno.list_species(db.session()).empty)
            roger.backend.geneanno.add_species(db.session(),
                                               roger.backend.geneanno.human_dataset,
                                               roger.backend.geneanno.human_tax_id)
            self.assertTrue(len(roger.backend.geneanno.list_species(db.session())) == 1)
            self.assertTrue(len(db.session().query(roger.backend.geneanno.Ortholog).limit(5).all()) > 0)
            roger.backend.geneanno.add_species(db.session(), rat_dataset, rat_tax_id)
            self.assertTrue(len(roger.backend.geneanno.list_species(db.session())) == 2)
            roger.backend.geneanno.remove_species(db.session(), rat_tax_id)
            self.assertTrue(len(roger.backend.geneanno.list_species(db.session())) == 1)
            db.drop_all()


if __name__ == '__main__':
    unittest.main()
