from tests import app
from tests import db

import roger.logic
import roger.logic.mart
import roger.persistence.dge


class TestDGEMethodsPersistence(object):

    def test_list_and_create_dge_method(self):
        with app.app_context():
            db.create_all()
            assert roger.persistence.dge.list_methods(db.session()).empty
            roger.persistence.dge.add_method(db.session(), "DGEMethod1", "DGE method", "0.1")
            assert len(roger.persistence.dge.list_methods(db.session())) == 1
            db.drop_all()
