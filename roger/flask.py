from flask import Flask
import tempfile
import os

from roger.persistence import db
import roger.rest.rest
import roger.logic
import roger.logic.mart.provider


# TODO: Find a better way to pass --config option value to this factory
def create_app(script_info):
    del script_info
    app = Flask('roger')
    app.config['ROGER_DATA_FOLDER'] = tempfile.mkdtemp()
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2 GB
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if 'ROGER_CONFIG' in os.environ:
        app.config.from_pyfile(os.environ['ROGER_CONFIG'], silent=True)
        roger.rest.rest.decorate_app(app)
        db.init_app(app)
        roger.logic.cache.init_app(app, config={'CACHE_TYPE': 'filesystem',
                                                'CACHE_DEFAULT_TIMEOUT': 60*60*24,
                                                'CACHE_DIR': os.path.join(app.config['ROGER_DATA_FOLDER'], "cache")})
        roger.logic.mart.provider.init_annotation_service(app)
    return app
