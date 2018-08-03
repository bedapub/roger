from flask import Flask
import os
import pytest

from roger.persistence import db
import roger.logic.mart.provider
import roger.persistence.geneanno
import roger.persistence.dge
import roger.logic.dge
from roger.persistence.schema import RNASeqDataSet, MicroArrayDataSet
from tests import mouse_dataset, mouse_tax_id

__script_location = os.path.realpath(__file__)
__roger_main_dir = os.path.split(os.path.split(__script_location)[0])[0]


def __create_test_app(db_url,
                      working_dir,
                      cache_dir) -> Flask:
    app = Flask('roger_test')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['ROGER_DATA_FOLDER'] = working_dir
    roger.logic.cache.init_app(app, config={'CACHE_TYPE': 'filesystem',
                                            'CACHE_DEFAULT_TIMEOUT': 60 * 60 * 24 * 2,
                                            'CACHE_DIR': cache_dir})
    roger.logic.mart.provider.init_annotation_service(app)
    db.init_app(app)
    return app


__in_memory_app = None
__app_with_datasets = None


def __init_db_with_datasets():
    init_test_db = True
    if os.path.exists("%s/__data/with_datasets/database.db" % __roger_main_dir):
        init_test_db = False
    app = __create_test_app("sqlite:///%s/__data/with_datasets/database.db" % __roger_main_dir,
                            "%s/__data/with_datasets/working_dir" % __roger_main_dir,
                            "%s/__data/with_datasets/cache" % __roger_main_dir)
    if init_test_db is True:
        print("Create test database 'with_dataset'")
        with app.app_context():
            db.create_all()
            session = db.session()
            roger.persistence.geneanno.add_species(session,
                                                   roger.persistence.geneanno.human_dataset,
                                                   roger.persistence.geneanno.human_tax_id)
            roger.persistence.geneanno.add_species(session, mouse_dataset, mouse_tax_id)
            roger.logic.dge.add_ds(session,
                                   app.config['ROGER_DATA_FOLDER'],
                                   MicroArrayDataSet,
                                   "test_data/ds/ma-example-signals.gct",
                                   mouse_tax_id,
                                   "affy_mouse430_2")

            roger.persistence.dge.add_design(session,
                                             "test_data/ds/ma-example-design.txt",
                                             "ma-example-signals")

            roger.persistence.dge.add_contrast(session,
                                               "test_data/ds/ma-example-contrast.txt",
                                               "ma-example-design",
                                               "ma-example-signals")

            roger.logic.dge.add_ds(session,
                                   app.config['ROGER_DATA_FOLDER'],
                                   RNASeqDataSet,
                                   "test_data/ds/rnaseq-example-readCounts.gct",
                                   roger.persistence.geneanno.human_tax_id,
                                   "entrezgene")

            roger.persistence.dge.add_design(session,
                                             "test_data/ds/rnaseq-example-DesignMatrix.txt",
                                             "rnaseq-example-readCounts")

            roger.persistence.dge.add_contrast(session,
                                               "test_data/ds/rnaseq-example-ContrastMatrix.txt",
                                               "rnaseq-example-DesignMatrix",
                                               "rnaseq-example-readCounts")

    return app


@pytest.fixture(scope="function")
def sqlite_in_memory():
    # TODO Refactor schema <-> SQAlchemy dependency in a way so this lazy creation is not necessary
    global __in_memory_app
    if __in_memory_app is None:
        __in_memory_app = __create_test_app("sqlite:///:memory:",
                                            "%s/__data/in_memory/working_dir" % __roger_main_dir,
                                            "%s/__data/in_memory/cache" % __roger_main_dir)
    with __in_memory_app.app_context():
        db.create_all()
        yield db
        db.drop_all()


@pytest.fixture(scope="module")
def sqlite_datasets():
    # TODO Refactor schema <-> SQAlchemy dependency in a way so this lazy creation is not necessary
    global __app_with_datasets
    if __app_with_datasets is None:
        __app_with_datasets = __init_db_with_datasets()
    with __app_with_datasets.app_context():
        yield db