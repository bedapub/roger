import unittest
from flask import Flask

import roger.logic
import roger.logic.mart
from roger.persistence import db
import roger.persistence.gse
import roger.persistence.geneanno

app = Flask('roger_test')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
roger.logic.mart.init_annotation_service(app)
roger.logic.cache.init_app(app, config={'CACHE_TYPE': 'simple'})


class TestGSEPersistence(unittest.TestCase):

    def test_list_and_create_gse_method(self):
        with app.app_context():
            db.create_all()
            self.assertTrue(roger.persistence.gse.list_methods(db.session()).empty)
            roger.persistence.gse.add_method(db.session(), "GSEMethod1", "GSE method", "0.1")
            self.assertTrue(len(roger.persistence.gse.list_methods(db.session())) == 1)
            db.drop_all()

    def test_list_and_create_gmt(self):
        with app.app_context():
            db.create_all()
            roger.persistence.geneanno.add_species(db.session(),
                                                   roger.persistence.geneanno.human_dataset,
                                                   roger.persistence.geneanno.human_tax_id)
            self.assertTrue(roger.persistence.gse.list_gmt(db.session()).empty)
            # TODO test file in __data is not part of open source distribution yet
            roger.persistence.gse.add_gmt(db.session(),
                                          "test_gmt",
                                          "../__data/gmt/test-userInput.gmt",
                                          roger.persistence.geneanno.human_tax_id)
            self.assertTrue(len(roger.persistence.gse.list_gmt(db.session())) == 1)
            roger.persistence.gse.delete_gmt(db.session(), "test_gmt")
            self.assertTrue(roger.persistence.gse.list_gmt(db.session()).empty)
            db.drop_all()


if __name__ == '__main__':
    unittest.main()
