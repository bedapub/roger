from tests import app
from tests import db

import roger.logic
import roger.logic.mart
import roger.persistence.gse
import roger.persistence.geneanno


class TestGSEPersistence(object):

    def test_list_and_create_gse_method(self):
        with app.app_context():
            db.create_all()
            assert roger.persistence.gse.list_methods(db.session()).empty
            roger.persistence.gse.add_method(db.session(), "GSEMethod1", "GSE method", "0.1")
            assert len(roger.persistence.gse.list_methods(db.session())) == 1
            db.drop_all()

    def test_list_and_create_gmt(self):
        with app.app_context():
            db.create_all()
            roger.persistence.geneanno.add_species(db.session(),
                                                   roger.persistence.geneanno.human_dataset,
                                                   roger.persistence.geneanno.human_tax_id)
            assert roger.persistence.gse.list_gmt(db.session()).empty
            # TODO tests file in __data is not part of open source distribution yet
            roger.persistence.gse.add_gmt(db.session(),
                                          "test_gmt",
                                          "../__data/gmt/tests-userInput.gmt",
                                          roger.persistence.geneanno.human_tax_id)
            assert len(roger.persistence.gse.list_gmt(db.session())) == 1
            roger.persistence.gse.delete_gmt(db.session(), "test_gmt")
            assert roger.persistence.gse.list_gmt(db.session()).empty
            db.drop_all()
