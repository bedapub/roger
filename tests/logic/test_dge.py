from pandas.util.testing import assert_frame_equal
from pandas import read_csv

from mock import patch
from roger.logic.dge import perform_edger
from tests import app, mouse_tax_id, mouse_dataset
from tests import db

from roger.util import parse_gct
import roger.logic
import roger.logic.mart
import roger.logic.geneanno
import roger.persistence.geneanno

from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from rpy2 import robjects


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

    @patch("roger.persistence.schema.RNASeqDataSet")
    def test_edger(self, ds_data):
        with app.app_context():
            #db.create_all()

            exprs_data_file = "test_data/ds/rnaseq-example-readCounts.gct"
            design_matrix = read_csv("test_data/ds/rnaseq-example-DesignMatrix.txt", sep="\t", index_col=0)
            contrast_matrix = read_csv("test_data/ds/rnaseq-example-ContrastMatrix.txt", sep="\t", index_col=0)
            fdf = read_csv("feature_anno.txt", sep="\t")

            ds_data.ExprsWC = exprs_data_file

            eset, eset_fit, dge_tbl, used_feature_names = perform_edger(ds_data, fdf, design_matrix, contrast_matrix)

            print(dge_tbl)

            #db.drop_all()
