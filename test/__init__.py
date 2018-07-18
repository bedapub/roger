from flask import Flask

from roger.persistence import db
import roger.logic.mart
import roger.persistence.geneanno

app = Flask('roger_test')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
roger.logic.mart.init_annotation_service(app)
roger.logic.cache.init_app(app, config={'CACHE_TYPE': 'simple'})
