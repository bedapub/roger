from flask import Blueprint, current_app
import re
import os.path
from flask import jsonify, make_response, request
from werkzeug.utils import secure_filename

from roger.logic.gse import get_gse_result
from roger.logic.util.exception import ROGERUsageError
from roger.persistence import db

ALLOWED_EXTENSIONS = {'gct', 'txt'}
IDENT_PATTERN = re.compile("^[a-zA-Z]\\w*$")

rest_api = Blueprint('api', __name__)


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


@rest_api.route('/gse/by_name/'
                '<string:study_name>/'
                '<string:design_name>/'
                '<string:contrast_name>/'
                '<string:dge_method_name>/'
                '<string:gse_method_name>',
                methods=['GET'])
def gse_table_by_name(study_name, design_name, contrast_name, dge_method_name, gse_method_name):
    session = db.session()
    gse_model = get_gse_result(session,  contrast_name, design_name, study_name, dge_method_name, gse_method_name)

    return make_response(gse_model.result_table.to_csv(index=False), 201)


@rest_api.route('/api/submitFull', methods=['POST'])
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
