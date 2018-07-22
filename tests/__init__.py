from flask import Flask

from roger.persistence import db
import roger.logic.mart.provider
import roger.persistence.geneanno

app = Flask('roger_test')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ROGER_DATA_FOLDER'] = "__data/roger_wd"
db.init_app(app)
roger.logic.mart.provider.init_annotation_service(app)
roger.logic.cache.init_app(app, config={'CACHE_TYPE': 'filesystem',
                                        'CACHE_DEFAULT_TIMEOUT': 60*60*24*2,
                                        'CACHE_DIR': "__data/roger_db/roger_test_cache"})
