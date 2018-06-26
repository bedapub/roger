import unittest
from flask import Flask

from roger import db
import roger.backend.gse
import roger.backend.geneanno

app = Flask('roger_test')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


class TestGSEPersistence(unittest.TestCase):

    def test_list_and_create_gse_method(self):
        with app.app_context():
            db.create_all()
            self.assertTrue(roger.backend.gse.list_methods(db.session()).empty)
            roger.backend.gse.add_method(db.session(), "GSEMethod1", "GSE method", "0.1")
            self.assertTrue(len(roger.backend.gse.list_methods(db.session())) == 1)
            db.drop_all()

    def test_list_and_create_gmt(self):
        with app.app_context():
            db.create_all()
            roger.backend.geneanno.add_species(db.session(),
                                               roger.backend.geneanno.human_dataset,
                                               roger.backend.geneanno.human_tax_id)
            self.assertTrue(roger.backend.gse.list_gmt(db.session()).empty)
            roger.backend.gse.add_gmt(db.session(), "test_gmt",
                                      "../__data/gmt/test-userInput.gmt",
                                      roger.backend.geneanno.human_tax_id)
            self.assertTrue(len(roger.backend.gse.list_gmt(db.session())) == 1)
            roger.backend.gse.delete_gmt(db.session(), "test_gmt")
            self.assertTrue(roger.backend.gse.list_gmt(db.session()).empty)
            db.drop_all()


if __name__ == '__main__':
    unittest.main()
