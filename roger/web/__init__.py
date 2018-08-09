import base64
import tempfile

from flask import Blueprint, render_template

from roger.persistence.dge import get_all_ds, get_model_by_id
from roger.persistence import db

from rpy2.robjects.packages import importr

ribios_utils = importr("ribiosUtils")
ribios_plot = importr("ribiosPlot")
ribios_ngs = importr("ribiosNGS")
ribios_expression = importr("ribiosExpression")
base = importr("base")
limma = importr("limma")
stats = importr("stats")
made4 = importr("made4")
graphics = importr("graphics")

web = Blueprint('web', __name__, template_folder='templates')


@web.route('/')
@web.route('/index')
def index():
    studies = get_all_ds(db.session())
    return render_template('index.html', studies=studies)


def gen_base64_plot(plot_opr):
    plot_fd, plot_file_path = tempfile.mkstemp(suffix=".png")
    ribios_utils.openFileDevice(plot_file_path, width=15, height=15)
    plot_opr()
    ribios_utils.closeFileDevice()

    with open(plot_file_path, "rb") as image_file:
        return str(base64.b64encode(image_file.read()), "utf-8")


@web.route('/dge_result/<int:contrast_id>/<int:method_id>')
def dge_result(contrast_id, method_id):
    model = get_model_by_id(contrast_id, method_id)
    obj = base.readRDS(model.InputObjFile)
    dge_test = base.readRDS(model.FitObjFile)

    # Pre-computation
    obj_mod_log_cmp = ribios_ngs.modLogCPM(dge_test)
    # groupLabels = ribios_expression.dispGroups(dge_test)
    # groupCol = ribios_plot.fcbrewer(groupLabels)
    obj_pca = stats.prcomp(base.t(obj_mod_log_cmp))
    obj_coa = made4.ord(obj_mod_log_cmp).rx2("ord").rx2("co")

    pairs_plot = None
    if base.ncol(ribios_expression.contrastMatrix(dge_test))[0] > 1:
        pairs_plot = gen_base64_plot(lambda: graphics.pairs(dge_test, freeRelation=True))

    return render_template('dge_result.html',
                           model=model,
                           mds_plot=gen_base64_plot(lambda: limma.plotMDS(dge_test, main="MDS plot")),
                           pca_plot=gen_base64_plot(lambda: ribios_plot.plotPCA(obj_pca,
                                                                                points=False,
                                                                                text=True,
                                                                                main="modLogCPM PCA")),
                           cda_plot=gen_base64_plot(lambda: made4.plotarrays(obj_coa,
                                                                             classvec=ribios_expression.dispGroups(
                                                                                 dge_test))),
                           norm_boxplot=gen_base64_plot(lambda: ribios_ngs.normBoxplot(obj, dge_test)),
                           bcv_plot=gen_base64_plot(lambda: ribios_ngs.plotBCV(dge_test, main="BCV plot")),
                           volcano_plot=gen_base64_plot(lambda: ribios_ngs.volcanoPlot(dge_test)),
                           smear_plot=gen_base64_plot(lambda: ribios_ngs.smearPlot(dge_test,
                                                                                   freeRelation=True,
                                                                                   smooth_scatter=False)),
                           pairs_plot=pairs_plot)