from flask import Blueprint, current_app
import re
import os.path
import numpy
from flask import jsonify, make_response, request
from flask_restful import Resource, fields, Api, marshal
from werkzeug.utils import secure_filename
from rpy2.robjects.packages import importr

from roger.logic import cache
from roger.logic.gse import get_gse_result
from roger.logic.util.common import merge_dicts
from roger.logic.util.exception import ROGERUsageError
from roger.persistence import db
from roger.persistence.dge import get_all_ds, get_ds, get_dge_model

ALLOWED_EXTENSIONS = {'gct', 'txt'}
IDENT_PATTERN = re.compile("^[a-zA-Z]\\w*$")

rest_blueprint = Blueprint('api', __name__)
api = Api(rest_blueprint)

ribios_plot = importr("ribiosPlot")
ribios_ngs = importr("ribiosNGS")
ribios_expression = importr("ribiosExpression")
base = importr("base")
limma = importr("limma")
stats = importr("stats")
made4 = importr("made4")
graphics = importr("graphics")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_ident(form_field):
    # check if the post request has the file part
    if form_field not in request.values:
        raise ROGERUsageError('No \'%s\' part' % form_field)
    value = request.values[form_field]
    # if user does not select file, browser also
    # submit a empty part without filename
    if not IDENT_PATTERN.match(value):
        raise ROGERUsageError("Invalid value for `%s': `%s`" % (form_field, value))
    return value


def get_file(form_field):
    # check if the post request has the file part
    if form_field not in request.files:
        raise ROGERUsageError('No \'%s\' part' % form_field)
    file = request.files[form_field]
    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        raise ROGERUsageError('No file specified for `%s`' % form_field)
    if not allowed_file(file.filename):
        raise ROGERUsageError("Invalid file name in `%s`: %s" % (form_field, file.filename))

    filename = secure_filename(file.filename)
    file.save(os.path.join(current_app().config['ROGER_DATA_FOLDER'], filename))
    return file


# -----------------
# GSE model
# -----------------


class GSETableCSVView(Resource):
    def get(self, study_name, design_name, contrast_name, dge_method_name, gse_method_name):
        session = db.session()
        gse_model = get_gse_result(session, contrast_name, design_name, study_name, dge_method_name, gse_method_name)

        return make_response(gse_model.result_table.to_csv(index=False), 201)


api.add_resource(GSETableCSVView,
                 '/study/<string:study_name>'
                 '/design/<string:design_name>'
                 '/contrast/<string:contrast_name>'
                 '/dge/<string:dge_method_name>'
                 '/gse/<string:gse_method_name>/tbl/csv')


class GSETableJSONView(Resource):
    def get(self, study_name, design_name, contrast_name, dge_method_name, gse_method_name):
        session = db.session()
        gse_model = get_gse_result(session, contrast_name, design_name, study_name, dge_method_name, gse_method_name)

        return make_response(gse_model.result_table.to_json(orient="table"), 201)


api.add_resource(GSETableJSONView,
                 '/study/<string:study_name>'
                 '/design/<string:design_name>'
                 '/contrast/<string:contrast_name>'
                 '/dge/<string:dge_method_name>'
                 '/gse/<string:gse_method_name>/tbl/json')

# -----------------
# DGE plots
# -----------------


def quantileRange(x, outlier=0.01, symmetric=True):
    quants = [outlier / 2, 1 - outlier / 2]
    qts = x.quantile(quants)
    if symmetric:
        mm = max(abs(qts))
        return [-mm, mm]
    return qts.tolist()


def gen_voncano_plot(contrast_column_id, dge_table, contrast_columns, x_range, y_range):
    single_table = dge_table[dge_table.ContrastColumnID == contrast_column_id]
    neg_log10_pvalue = -numpy.log10(single_table.PValue)
    log_fc = single_table.LogFC

    data = {'x': log_fc.tolist(),
            'y': neg_log10_pvalue.tolist(),
            'text': dge_table.GeneSymbol.tolist(),
            'type': 'scatter',
            'mode': 'markers'}
    layout = {
        "xaxis": {
            "title": "logFC",
            "range": x_range,
            "showline": True,
        },
        "yaxis": {
            "title": "-log10(PValue)",
            "range": y_range,
            "showline": True,
        },
        "width": 500,
        "height": 500,
        "title": contrast_columns[contrast_columns.ID == contrast_column_id].Name.values[0]
    }
    return {'data': [data], 'layout': layout}


class DGE_Plot_Volcano(Resource):
    @cache.cached()
    def get(self, study_name, design_name, contrast_name, dge_method_name):
        session = db.session()
        dge_model = get_dge_model(session,
                                  contrast_name,
                                  design_name,
                                  study_name,
                                  dge_method_name)
        dge_table = dge_model.result_table
        feature_data = dge_model.Contrast.Design.DataSet.feature_data
        contrast_columns = dge_model.Contrast.contrast_columns

        dge_table = dge_table.join(contrast_columns.set_index('ID'), on='ContrastColumnID', rsuffix="Contrast", )
        dge_table = dge_table.join(feature_data.set_index('FeatureIndex'), on='FeatureIndex', rsuffix="Feature", )

        neg_log10_pvalue = -numpy.log10(dge_table.PValue)
        log_fc = dge_table.LogFC

        x_range = quantileRange(log_fc, symmetric=True)
        y_range = [0, max(quantileRange(neg_log10_pvalue, symmetric=False))]

        plots = [gen_voncano_plot(contrastColumnId, dge_table, contrast_columns, x_range, y_range)
                 for contrastColumnId in set(dge_table.ContrastColumnID)]

        return jsonify(plots)


api.add_resource(DGE_Plot_Volcano,
                 '/study/<string:study_name>'
                 '/design/<string:design_name>'
                 '/contrast/<string:contrast_name>'
                 '/dge/<string:dge_method_name>/plot/volcano')


class DGE_Plot_PCA(Resource):
    @cache.cached()
    def get(self, study_name, design_name, contrast_name, dge_method_name):
        session = db.session()
        dge_model = get_dge_model(session,
                                  contrast_name,
                                  design_name,
                                  study_name,
                                  dge_method_name)

        obj = base.readRDS(dge_model.InputObjFile)
        # Pre-computation
        obj_mod_log_cmp = ribios_ngs.modLogCPM(obj)
        obj_pca = stats.prcomp(base.t(obj_mod_log_cmp))
        points = base.as_data_frame(ribios_plot.pcaScores(obj_pca))
        xind = 0
        yind = 1
        sdev_norm = sum([sdev * sdev for sdev in obj_pca.rx2("sdev")])
        expvar = [sdev * sdev / sdev_norm for sdev in obj_pca.rx2("sdev")]
        data = [{
            "x": [x for x in points[0]],
            "y": [y for y in points[1]],
            "mode": 'markers',
            "type": 'scatter',
            "name": 'Data Points',
            "text": [name for name in base.rownames(points)]
        }]
        layout = {
            "xaxis": {
                "title": "Principal component %d (%2.1f%%)" % (xind + 1, expvar[xind] * 100),
                "showline": True,
            },
            "yaxis": {
                "title": "Principal component %d (%2.1f%%)" % (yind + 1, expvar[yind] * 100),
                "showline": True,
            },
            "width": 500,
            "height": 500,
            "title": 'modLogCPM PCA'
        }

        return jsonify({'data': data, 'layout': layout})


api.add_resource(DGE_Plot_PCA,
                 '/study/<string:study_name>'
                 '/design/<string:design_name>'
                 '/contrast/<string:contrast_name>'
                 '/dge/<string:dge_method_name>/plot/pca')

# -----------------
# DGE results
# -----------------


DGEModelViewFields = {
    'MethodName': fields.String(attribute="Method.Name"),
    'MethodDescription': fields.String,
}


class DGETopTableCSVView(Resource):
    def get(self, study_name, design_name, contrast_name, dge_method_name):
        session = db.session()
        dge_model = get_dge_model(session, contrast_name, design_name, study_name, dge_method_name)

        return make_response(dge_model.result_table.to_csv(index=False), 201)


api.add_resource(DGETopTableCSVView,
                 '/study/<string:study_name>'
                 '/design/<string:design_name>'
                 '/contrast/<string:contrast_name>'
                 '/dge/<string:dge_method_name>/tbl/csv')


class DGETopTableJSONView(Resource):
    def get(self, study_name, design_name, contrast_name, dge_method_name):
        session = db.session()
        dge_model = get_dge_model(session, contrast_name, design_name, study_name, dge_method_name)

        return make_response(dge_model.result_table.to_json(orient="table"), 201)


api.add_resource(DGETopTableJSONView,
                 '/study/<string:study_name>'
                 '/design/<string:design_name>'
                 '/contrast/<string:contrast_name>'
                 '/dge/<string:dge_method_name>/tbl/json')

class FeatureSubsetJSONView(Resource):
    def get(self, study_name, design_name, contrast_name, dge_method_name):
        session = db.session()
        dge_model = get_dge_model(session, contrast_name, design_name, study_name, dge_method_name)

        return make_response(dge_model.feature_subset_table.to_json(orient="table"), 201)


api.add_resource(FeatureSubsetJSONView,
                 '/study/<string:study_name>'
                 '/design/<string:design_name>'
                 '/contrast/<string:contrast_name>'
                 '/dge/<string:dge_method_name>/feature_subset/json')


class FeatureSubsetCSVView(Resource):
    def get(self, study_name, design_name, contrast_name, dge_method_name):
        session = db.session()
        dge_model = get_dge_model(session, contrast_name, design_name, study_name, dge_method_name)

        return make_response(dge_model.feature_subset_table.to_csv(index=False), 201)


api.add_resource(FeatureSubsetCSVView,
                 '/study/<string:study_name>'
                 '/design/<string:design_name>'
                 '/contrast/<string:contrast_name>'
                 '/dge/<string:dge_method_name>/feature_subset/csv')

# -----------------
# Design
# -----------------


GSEResultViewFields = {
    'GSEMethodName': fields.String(attribute="GSEMethod.Name"),
    'DGEMethodName': fields.String(attribute="DGEMethod.Name"),
    'MethodDescription': fields.String,
    'OutputFile': fields.String
}

ContrastColumnViewFields = {
    'Name': fields.String,
    'Description': fields.String,
    'ColumnData': fields.Raw,
}

ContrastViewFields = {
    'Name': fields.String,
    'Description': fields.String,
    'CreatedBy': fields.String,
    'CreationTime': fields.DateTime(dt_format='rfc822'),
    'ContrastColumn': fields.List(fields.Nested(ContrastColumnViewFields)),
    'DGEmodel': fields.List(fields.Nested(DGEModelViewFields)),
    'GSEresult': fields.List(fields.Nested(GSEResultViewFields))
}

DesignsViewFields = {
    'Name': fields.String(),
    'Description': fields.String(),
    'VariableCount': fields.Integer(),
    'CreatedBy': fields.String(),
    'CreationTime': fields.DateTime(dt_format='rfc822'),
    'LastReviewedBy': fields.String(),
}

SampleSubsetViewFields = {
    'SampleIndex': fields.Integer,
    'IsUsed': fields.Boolean,
    'Description': fields.String
}

DesignViewFields = merge_dicts(DesignsViewFields, {
    'SampleSubset': fields.List(fields.Nested(SampleSubsetViewFields)),
    'Contrast': fields.List(fields.Nested(ContrastViewFields)),
    'SampleGroups': fields.Raw(),
    'SampleGroupLevels': fields.Raw(),
    'DesignMatrix': fields.Raw()
})

# -----------------
# Data set
# -----------------

StudiesViewFields = {
    'Name': fields.String(),
    'GeneAnnotationVersion': fields.String(),
    'ExpressionType': fields.String(attribute='Type.name'),
    'Description': fields.String(),
    'FeatureCount': fields.Integer(),
    'SampleCount': fields.Integer(),
    'TaxID': fields.Integer(),
    'Xref': fields.String(),
    'CreatedBy': fields.String(),
    'CreationTime': fields.DateTime(dt_format='rfc822'),
    'URL': fields.Url('api.studyview', absolute=True)
}


class StudiesView(Resource):
    def get(self):
        session = db.session()
        result_table = get_all_ds(session)

        return marshal(result_table, StudiesViewFields)


api.add_resource(StudiesView,
                 '/study')

StudyViewFields = merge_dicts(StudiesViewFields, {
    'ExprsFile': fields.String(attribute='ExprsSrc'),
    'PhenoFile': fields.String(attribute='PhenoSrc'),
    'ExprsTable': fields.Url('api.exprsview', absolute=True),
    'FeatureAnnotationTable': fields.Url('api.featureannotationview', absolute=True),
    'SampleAnnotationExprsTable': fields.Url('api.sampleannotationjsonview', absolute=True),
    'Design': fields.List(fields.Nested(DesignViewFields))
})


class StudyView(Resource):
    def get(self, Name):
        session = db.session()
        study = get_ds(session, Name)

        return marshal(study, StudyViewFields)


api.add_resource(StudyView,
                 '/study/<string:Name>')


class ExprsView(Resource):
    def get(self, Name):
        session = db.session()
        study = get_ds(session, Name)

        return make_response(study.exprs_data.to_csv(), 201)


api.add_resource(ExprsView,
                 '/study/<string:Name>/exprs')


class SampleAnnotationJsonView(Resource):
    def get(self, Name):
        session = db.session()
        study = get_ds(session, Name)

        return make_response(study.pheno_data.to_json(orient="table"), 201)


api.add_resource(SampleAnnotationJsonView,
                 '/study/<string:Name>/sample_annotation/json')


class SampleAnnotationCSVView(Resource):
    def get(self, Name):
        session = db.session()
        study = get_ds(session, Name)

        return make_response(study.pheno_data.to_csv(index=False), 201)


api.add_resource(SampleAnnotationCSVView,
                 '/study/<string:Name>/sample_annotation/csv')


class FeatureAnnotationCSVView(Resource):
    def get(self, Name):
        session = db.session()
        study = get_ds(session, Name)

        return make_response(study.feature_data.to_csv(index=False), 201)


api.add_resource(FeatureAnnotationCSVView,
                 '/study/<string:Name>/feature_annotation/csv')


class FeatureAnnotationJSONView(Resource):
    def get(self, Name):
        session = db.session()
        study = get_ds(session, Name)

        return make_response(study.feature_data.to_json(orient="table"), 201)


api.add_resource(FeatureAnnotationJSONView,
                 '/study/<string:Name>/feature_annotation/json')
