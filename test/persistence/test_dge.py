import unittest

from test import app
from test import db

import roger.logic
import roger.logic.mart
import roger.persistence.dge


class TestDGEmethodsPersistence(unittest.TestCase):

    def test_list_and_create_dge_method(self):
        with app.app_context():
            db.create_all()
            self.assertTrue(roger.persistence.dge.list_methods(db.session()).empty)
            roger.persistence.dge.add_method(db.session(), "DGEMethod1", "DGE method", "0.1")
            self.assertTrue(len(roger.persistence.dge.list_methods(db.session())) == 1)
            db.drop_all()


if __name__ == '__main__':
    unittest.main()
