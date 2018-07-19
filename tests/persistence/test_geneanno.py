from tests import app
from tests import db

import roger.logic.mart
import roger.persistence.geneanno

rat_dataset = "rnorvegicus_gene_ensembl"
rat_tax_id = 10116


class TestGeneAnnotationPersistence(object):

    def test_list_species_and_import(self):
        with app.app_context():
            db.create_all()
            assert roger.persistence.geneanno.list_species(db.session()).empty
            roger.persistence.geneanno.add_species(db.session(),
                                                   roger.persistence.geneanno.human_dataset,
                                                   roger.persistence.geneanno.human_tax_id)
            assert len(roger.persistence.geneanno.list_species(db.session())) == 1
            assert len(db.session().query(roger.persistence.geneanno.Ortholog).limit(5).all()) > 0
            roger.persistence.geneanno.add_species(db.session(), rat_dataset, rat_tax_id)
            assert len(roger.persistence.geneanno.list_species(db.session())) == 2
            roger.persistence.geneanno.remove_species(db.session(), rat_tax_id)
            assert len(roger.persistence.geneanno.list_species(db.session())) == 1
            db.drop_all()
