from flask import Flask, send_from_directory
import tempfile
import os
import sys

from roger.persistence import db


# TODO: Find a better way to pass --config option value to this factory
def create_app(script_info):
    # not used at the moment
    del script_info
    app = Flask('roger')
    app.config['ROGER_DATA_FOLDER'] = tempfile.mkdtemp()
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2 GB
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True
    if 'ROGER_CONFIG' in os.environ:
        from flask_cors import CORS
        import roger.logic
        import roger.logic.mart.provider

        cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

        app.config.from_pyfile(os.environ['ROGER_CONFIG'], silent=True)
        db.init_app(app)
        roger.logic.cache.init_app(app, config={'CACHE_TYPE': 'filesystem',
                                                'CACHE_DEFAULT_TIMEOUT': 60*60*24,
                                                'CACHE_DIR': os.path.join(app.config['ROGER_DATA_FOLDER'], "cache")})
        roger.logic.mart.provider.init_annotation_service(app)

        if len(sys.argv) > 1 and sys.argv[1] in ["run", "shell"]:
            from roger.web import web_blueprint
            from roger.rest import rest_blueprint
            from roger.logic.util.exception import ROGERUsageError
            from flask import make_response, jsonify

            # TODO: Make error handlers that do not always return json responses.
            @app.errorhandler(ROGERUsageError)
            def handle_invalid_usage(error):
                response = jsonify(error.to_dict())
                response.status_code = error.status_code
                return response

            @app.errorhandler(404)
            def not_found(error):
                # not used
                del error
                return make_response(jsonify({'error': 'Not found'}), 404)

            @app.errorhandler(405)
            def not_allowed(error):
                # not used
                del error
                return make_response(jsonify({'error': 'Method Not Allowed'}), 405)

            @app.route('/static/', defaults={'path': ''})
            @app.route('/static/<path:path>')
            def get_resource(path):  # pragma: no cover
                return send_from_directory('static', path)

            app.register_blueprint(rest_blueprint, url_prefix='/api')
            app.register_blueprint(web_blueprint, url_prefix='/')

    return app
