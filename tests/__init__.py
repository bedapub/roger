from flask import Flask

from roger.persistence import db
import roger.logic.mart.provider
import roger.persistence.geneanno

mouse_dataset = "mmusculus_gene_ensembl"
mouse_tax_id = 10090
rat_dataset = "rnorvegicus_gene_ensembl"
rat_tax_id = 10116


app = Flask('roger_test')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ROGER_DATA_FOLDER'] = "__data/roger_wd"
db.init_app(app)
roger.logic.mart.provider.init_annotation_service(app)
roger.logic.cache.init_app(app, config={'CACHE_TYPE': 'filesystem',
                                        'CACHE_DEFAULT_TIMEOUT': 60 * 60 * 24 * 2,
                                        'CACHE_DIR': "__data/roger_db/roger_test_cache"})
