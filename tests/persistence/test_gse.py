import flask

import roger.logic
import roger.logic.mart
import roger.persistence.dge
import roger.persistence.gse
import roger.persistence.geneanno


class TestGSEPersistence(object):

    def test_list_and_create_gse_method(self, sqlite_in_memory):
        session = sqlite_in_memory.session()
        assert roger.persistence.gse.list_methods(session).empty
        dge_method = roger.persistence.dge.add_method(session, "DGEMethod", "DGE method")
        roger.persistence.gse.add_method(session, dge_method, "GSEMethod1", "GSE method")
        assert len(roger.persistence.gse.list_methods(session)) == 1

    def test_list_and_create_gmt(self, sqlite_in_memory):
        session = sqlite_in_memory.session()

        gmt_cat_name = "dummy_gmt"
        roger.persistence.geneanno.add_species(session,
                                               roger.persistence.geneanno.human_dataset,
                                               roger.persistence.geneanno.human_tax_id)
        assert roger.persistence.gse.list_gmt(session).empty
        # TODO tests file in __data is not part of open source distribution yet
        roger.persistence.gse.add_gmt(session,
                                      flask.current_app.config['ROGER_DATA_FOLDER'],
                                      gmt_cat_name,
                                      "test_data/gmt/dummy.gmt",
                                      roger.persistence.geneanno.human_tax_id)
        assert len(roger.persistence.gse.list_gmt(session)) == 1
        roger.persistence.gse.delete_gmt(session, gmt_cat_name)
        assert roger.persistence.gse.list_gmt(session).empty
