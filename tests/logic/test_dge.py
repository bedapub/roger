from pandas.util.testing import assert_frame_equal
from pandas import read_csv

from tests import app, mouse_tax_id, mouse_dataset
from tests import db

from roger.util import parse_gct
import roger.logic
import roger.logic.mart
import roger.logic.geneanno
import roger.persistence.geneanno


class TestDGEAnalysis(object):

    # def test_limma(self):
    #     with app.app_context():
    #         db.create_all()
    #
    #         session = db.session()
    #         roger.persistence.geneanno.add_species(session,
    #                                                roger.persistence.geneanno.human_dataset,
    #                                                roger.persistence.geneanno.human_tax_id)
    #         roger.persistence.geneanno.add_species(session,
    #                                                mouse_dataset,
    #                                                mouse_tax_id)
    #
    #         gct_data = parse_gct(file_path="test_data/ds/ma-example-signals.gct")
    #         (feature_data, annotation_version) = roger.logic.geneanno.annotate(session,
    #                                                                            gct_data,
    #                                                                            mouse_tax_id,
    #                                                                            "affy_mouse430_2")
    #         assert "Mouse genes" in annotation_version
    #         assert_frame_equal(read_csv("test_data/ds/ma-example-rogerFeatureAnno.txt", sep="\t", index_col=0),
    #                            feature_data)
    #         db.drop_all()

    def test_edger(self):
        with app.app_context():
            db.create_all()

            #session = db.session()
            #roger.persistence.geneanno.add_species(session,
            #                                       roger.persistence.geneanno.human_dataset,
            #                                       roger.persistence.geneanno.human_tax_id)

            gct_data = parse_gct(file_path="test_data/ds/rnaseq-example-readCounts.gct")
            #read_table(self.PhenoWC, sep='\t')
            design_data = parse_gct(file_path="test_data/ds/rnaseq-example-readCounts.gct")


            #assert "Human genes" in annotation_version
            #assert_frame_equal(read_csv("test_data/ds/rnaseq-example-rogerFeatureAnno.txt", sep="\t", index_col=0),
            #                   feature_data)

            db.drop_all()
