from roger.logic.util.exception import ROGERUsageError

import re
import os.path
from flask import jsonify, make_response, request
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'gct', 'txt'}
IDENT_PATTERN = re.compile("^[a-zA-Z]\\w*$")


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


def decorate_app(roger_app):
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
        file.save(os.path.join(roger_app.config['ROGER_DATA_FOLDER'], filename))
        return file

    @roger_app.route('/api/submitFull', methods=['POST'])
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

    @roger_app.errorhandler(ROGERUsageError)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @roger_app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    @roger_app.errorhandler(405)
    def not_found(error):
        return make_response(jsonify({'error': 'Method Not Allowed'}), 405)

