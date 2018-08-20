import pytest
from flask_sqlalchemy import SQLAlchemy
from rpy2.robjects.packages import importr

from roger.logic.gse import EdgeRCamera

base = importr("base")
ribios_gsea = importr("ribiosGSEA")


class TestGSEAnalysisWith(object):
    @pytest.mark.skip(reason="Not Implemented")
    @pytest.mark.parametrize("algorithm, contrast_name, design_name, ds_name, dge_method_name, fit_obj_file, expected_dge_file", [
        (EdgeRCamera(),
         "ma-example-contrast",
         "ma-example-design",
         "ma-example-signals",
         "test_data/edger_fit_obj.rds",
         "edgeR",
         "__data/camera-expected-edger.txt"),
    ])
    def test_ges_algorithms(self, sqlite_datasets: SQLAlchemy):
        dge_model_path = "test_data/edger_fit_obj.rds"
        dge_model = base.readRDS(dge_model_path)

        gmt_path = "__data/gmt"
        gscs = ribios_gsea.readDefaultGenesets(gmt_path)

        #exec_gse(dge_model, gscs)
