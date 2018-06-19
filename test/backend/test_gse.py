import unittest
from flask import Flask

from roger import db
from roger.backend.geneanno import human_tax_id
import roger.backend.gse

app = Flask('roger_test')
#app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///../__data/roger_db/test-roger-schema.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


class TestGSEmethodsPersistence(unittest.TestCase):

    # TODO
    @unittest.skip("TODO skip for testing")
    def test_list_and_create_gse_method(self):
        with app.app_context():
            db.create_all()
            self.assertTrue(roger.backend.gse.list_methods(db.session()).empty)
            roger.backend.gse.add_method(db.session(), "GSEMethod1", "GSE method", "0.1")
            self.assertTrue(len(roger.backend.gse.list_methods(db.session())) == 1)
            db.drop_all()

    # TODO
    @unittest.skip("TODO skip for testing")
    def test_list_and_create_gmt(self):
        with app.app_context():
            print(roger.backend.gse.list_gmt(db.session()))
            print(roger.backend.gse.delete_gmt(db.session(), "test_gmt"))
            #print(roger.backend.gse.list_gmt(db.session()))
            #roger.backend.gse.add_gmt(db.session(), "test_gmt",
            #                          "../data/gmt/homo-sapiens-9606-gene-symbol.gmt",
            #                          human_tax_id)
            #db.create_all()
            #self.assertTrue(roger.backend.dge.list_methods(db.session()).empty)
            #roger.backend.dge.add_method(db.session(), "DGEMethod1", "DGE method", "0.1")
            #self.assertTrue(len(roger.backend.dge.list_methods(db.session())) == 1)
            #db.drop_all()


if __name__ == '__main__':
    unittest.main()
