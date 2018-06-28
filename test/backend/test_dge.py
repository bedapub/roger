import unittest
from flask import Flask

from roger.main import db
import roger.backend.dge

app = Flask('roger_test')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


class TestDGEmethodsPersistence(unittest.TestCase):

    def test_list_and_create_dge_method(self):
        with app.app_context():
            db.create_all()
            self.assertTrue(roger.backend.dge.list_methods(db.session()).empty)
            roger.backend.dge.add_method(db.session(), "DGEMethod1", "DGE method", "0.1")
            self.assertTrue(len(roger.backend.dge.list_methods(db.session())) == 1)
            db.drop_all()


if __name__ == '__main__':
    unittest.main()
