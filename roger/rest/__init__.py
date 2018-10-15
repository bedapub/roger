from flask import Blueprint, current_app
import re
import os.path
from flask import jsonify, make_response, request
from flask_restful import Resource, fields, Api, marshal
from werkzeug.utils import secure_filename

from roger.logic.gse import get_gse_result
from roger.logic.util.common import merge_dicts
from roger.logic.util.exception import ROGERUsageError
from roger.persistence import db
from roger.persistence.dge import get_all_ds, get_ds, get_all_design, get_design

ALLOWED_EXTENSIONS = {'gct', 'txt'}
IDENT_PATTERN = re.compile("^[a-zA-Z]\\w*$")

rest_blueprint = Blueprint('api', __name__)
api = Api(rest_blueprint)


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
    'SampleAnnotationExprsTable': fields.Url('api.sampleannotationview', absolute=True),
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


class SampleAnnotationView(Resource):
    def get(self, Name):
        session = db.session()
        study = get_ds(session, Name)

        return make_response(study.pheno_data.to_csv(), 201)


api.add_resource(SampleAnnotationView,
                 '/study/<string:Name>/sample_annotation')


class FeatureAnnotationView(Resource):
    def get(self, Name):
        session = db.session()
        study = get_ds(session, Name)

        return make_response(study.feature_data.to_csv(), 201)


api.add_resource(FeatureAnnotationView,
                 '/study/<string:Name>/feature_annotation')

# -----------------
# Design
# -----------------

DGEModelViewFields = {
    'MethodName': fields.String(attribute="Method.Name"),
    'MethodDescription': fields.String,
}

GSEResultViewFields = {
    'GSEMethodName': fields.String(attribute="GSEMethod.Name"),
    'DGEMethodName': fields.String(attribute="DGEMethod.Name"),
    'MethodDescription': fields.String,
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


class DesignsView(Resource):
    def get(self, Name):
        session = db.session()
        designs = get_all_design(session, Name)

        return marshal(designs, DesignViewFields)


api.add_resource(DesignsView,
                 '/study/<string:Name>/design')


class DesignView(Resource):
    def get(self, design_name, study_name):
        session = db.session()
        design = get_design(session, design_name, study_name)

        return marshal(design, DesignViewFields)


api.add_resource(DesignView,
                 '/study/<string:study_name>/design/<string:design_name>')

# -----------------
# GSE
# -----------------


class GSETable(Resource):
    def get(self, study_name, design_name, contrast_name, dge_method_name, gse_method_name):
        session = db.session()
        gse_model = get_gse_result(session, contrast_name, design_name, study_name, dge_method_name, gse_method_name)

        return make_response(gse_model.result_table.to_csv(index=False), 201)


api.add_resource(GSETable,
                 '/gse/'
                 '<string:study_name>/'
                 '<string:design_name>/'
                 '<string:contrast_name>/'
                 '<string:dge_method_name>/'
                 '<string:gse_method_name>')


@rest_blueprint.route('/api/submitFull', methods=['POST'])
def get_tasks():
    userName = get_ident('username')
    jobName = get_ident('jobname')

    inputFile = get_file('infile')
    designFile = get_file('design')
    contrastFile = get_file('contrast')

    # timeStemp <- gsub("\\s|:|-","_", Sys.time())

    # dir.create(limmaWorkingDir, showWarnings = FALSE)

    # logFile <- sprintf("%s/%s__%s__%s.log", limmaWorkingDir, username, jobname, timeStemp)
    # outDir <- sprintf("%s/%s__%s__%s", limmaWorkingDir, username, jobname, timeStemp)

    # args <- c("-infile", infile,
    # "-design", design,
    # "-contrast", contrast,
    # "-log", logFile,
    # "-outdir", outDir,
    # "-debug")
    # system2(command=limmaPipelineCommand, args=args)
    # list(
    #  log = readLines(logFile),
    #  out_path = outDir
    # )
    return make_response(jsonify({'task': "asfs"}), 201)
