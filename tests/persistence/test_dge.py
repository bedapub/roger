import roger.logic
import roger.logic.mart
import roger.persistence.dge


class TestDGEMethodsPersistence(object):

    def test_list_and_create_dge_method(self, sqlite_in_memory):
        session = sqlite_in_memory.session()
        assert roger.persistence.dge.list_methods(session).empty
        roger.persistence.dge.add_method(session, "DGEMethod1", "DGE method")
        assert len(roger.persistence.dge.list_methods(session)) == 1
