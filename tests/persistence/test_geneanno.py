import pytest

from tests import rat_dataset, rat_tax_id
from roger.exception import ROGERUsageError
import roger.logic.mart
import roger.persistence.geneanno


class TestGeneAnnotationPersistence(object):

    def test_list_species_and_import(self, sqlite_in_memory):
        session = sqlite_in_memory.session()
        assert roger.persistence.geneanno.list_species(session).empty
        roger.persistence.geneanno.add_species(session,
                                               roger.persistence.geneanno.human_dataset,
                                               roger.persistence.geneanno.human_tax_id)
        assert len(roger.persistence.geneanno.list_species(session)) == 1
        assert len(session.query(roger.persistence.geneanno.Ortholog).limit(5).all()) > 0
        roger.persistence.geneanno.add_species(session, rat_dataset, rat_tax_id)
        assert len(roger.persistence.geneanno.list_species(session)) == 2

    @pytest.mark.skip(reason="TODO high performance problem with SQLite database")
    def test_import_and_delete_species(self, sqlite_in_memory):
        session = sqlite_in_memory.session()
        assert roger.persistence.geneanno.list_species(session).empty
        roger.persistence.geneanno.add_species(session,
                                               roger.persistence.geneanno.human_dataset,
                                               roger.persistence.geneanno.human_tax_id)
        assert len(roger.persistence.geneanno.list_species(session)) == 1
        assert len(session.query(roger.persistence.geneanno.Ortholog).limit(5).all()) > 0
        roger.persistence.geneanno.add_species(session, rat_dataset, rat_tax_id)
        assert len(roger.persistence.geneanno.list_species(session)) == 2
        roger.persistence.geneanno.remove_species(session, rat_tax_id)
        assert len(roger.persistence.geneanno.list_species(session)) == 1

    def test_fail_on_unknown_ds(self, sqlite_in_memory):
        session = sqlite_in_memory.session()
        assert roger.persistence.geneanno.list_species(session).empty
        with pytest.raises(ROGERUsageError):
            roger.persistence.geneanno.add_species(session,
                                                   "draco_gene_ensembl",
                                                   roger.persistence.geneanno.human_tax_id)
