# TODO Maybe move decorator-specific stuff (CLI-commands, REST endponts) to dedicated modules
from __future__ import print_function
import sys
import os
import os.path
import click
from flask import Flask
from flask.cli import FlaskGroup
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection
import tempfile
import getpass

import roger.rest
import roger.backend.geneanno
import roger.backend.gse
import roger.backend.dge
from roger.backend.schema import Model


# TODO move this to a appropriate location
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    del connection_record
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


db = SQLAlchemy(model_class=Model)


# TODO: Find a better way to pass --config option value to this factory
def create_app(script_info):
    del script_info
    app = Flask('roger')
    app.config['ROGER_DATA_FOLDER'] = tempfile.mkdtemp()
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2 GB
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if 'ROGER_CONFIG' in os.environ:
        app.config.from_pyfile(os.environ['ROGER_CONFIG'], silent=True)
        roger.rest.decorate_app(app)
        db.init_app(app)
    return app


@click.group(cls=FlaskGroup, create_app=create_app)
@click.option('--config', help='Pass ROGER configuration file')
def cli(config):
    """Management script for the ROGER application."""
    if config is not None:
        os.environ['ROGER_CONFIG'] = config
    if 'ROGER_CONFIG' not in os.environ or not os.environ['ROGER_CONFIG']:
        home = os.path.expanduser("~")
        os.environ['ROGER_CONFIG'] = os.path.join(home, ".roger_config.cfg")

    # Check if config file does exist
    config_file = os.environ['ROGER_CONFIG']
    if not os.path.isfile(config_file):
        print("Cannot open config file: %s" % config_file, file=sys.stderr)
        sys.exit(-1)

# --------------------------
# General stuff
# --------------------------


@cli.command(name="init-db", short_help='Initialize new ROGER instance')
def init_database():
    sys.stdout.write("Initializing database with human gene annotation data ...")
    sys.stdout.flush()
    roger.backend.init_db(db)
    print("Done")

# --------------------------
# Gene Annotation
# --------------------------


@cli.command(name="list-species", short_help='Lists all species with imported gene annotation data')
def list_species():
    """Used to retrieve a table of species whose gene annotation data has been imported into the database instance.
    """
    print(roger.backend.geneanno.list_species(db.session()))


@cli.command(name="add-species", short_help='Import gene annotation data from Ensembl BioMart dataset')
@click.argument('dataset', metavar='<dataset>')
@click.argument('tax_id', type=int, metavar='<tax_id>')
def add_species(dataset, tax_id):
    """Used to import gene annotation data from Ensembl from a specific dataset / species

    Example:
        roger import-geneanno rnorvegicus_gene_ensembl 10116
    """
    sys.stdout.write("Importing gene annotation for species %s ..." % tax_id)
    sys.stdout.flush()
    roger.backend.geneanno.add_species(db.session(), dataset, tax_id)
    print("Done")


@cli.command(name="remove-species", short_help='Removes gene annotation data from the database instance')
@click.argument('tax_id', type=int, metavar='<tax_id>')
def delete_gene_anno(tax_id):
    """Used to delete imported gene annotation data from the database
    """
    roger.backend.geneanno.remove_species(db.session(), tax_id)
    print("Deleted gene annotation for species %s" % tax_id)

# --------------------------
# GSE Methods
# --------------------------


@cli.command(name="list-gse-methods", short_help='Lists all GSE methods utilized in ROGER studies')
def list_gse_methods():
    print(roger.backend.gse.list_methods(db.session()))


@cli.command(name="add-gse-method", short_help='Adds a new GSE method to the database')
@click.argument('name', metavar='<name>')
@click.argument('description', metavar='<description>')
@click.argument('version', metavar='<version>')
def add_gse_method(name, description, version):
    roger.backend.gse.add_method(db.session(), name, description, version)
    print("Added GSE method: %s" % name)


@cli.command(name="remove-gse-method", short_help='Removes the GSE method with the given name')
@click.argument('name', metavar='<name>')
def delete_gse_method(name):
    roger.backend.gse.delete_method(db.session(), name)
    print("Deleted GSE method: %s" % name)


@cli.command(name="list-small", short_help='Lists all gene set categories and their number of gene sets')
def list_gmt():
    print(roger.backend.gse.list_gmt(db.session()))


@cli.command(name="add-small", short_help='Adds a GMT file into the ROGER instance')
@click.argument('category_name', metavar='<category_name>')
@click.argument('gmt_file', metavar='<gmt_file>')
@click.argument('tax_id', metavar='<tax_id>')
def add_gmt(category_name, gmt_file, tax_id):
    sys.stdout.write("Importing gene sets from GMT file '%s' ..." % gmt_file)
    sys.stdout.flush()
    roger.backend.gse.add_gmt(db.session(), category_name, gmt_file, tax_id)
    print("Done")


@cli.command(name="remove-small", short_help='Removes all gene sets associated with the given gene sete category')
@click.argument('category_name', metavar='<category_name>')
def delete_gse_method(category_name):
    roger.backend.gse.delete_gmt(db.session(), category_name)
    print("Deleted gene set category: %s" % category_name)

# --------------------------
# DGE Methods
# --------------------------


@cli.command(name="list-dge-methods", short_help='Lists all DGE methods utilized in ROGER studies')
def list_dge_methods():
    print(roger.backend.dge.list_methods(db.session()))


@cli.command(name="add-dge-method", short_help='Adds a new DGE method to the database')
@click.argument('name', metavar='<name>')
@click.argument('description', metavar='<description>')
@click.argument('version', metavar='<version>')
def add_dge_method(name, description, version):
    roger.backend.dge.add_method(db.session(), name, description, version)
    print("Added DGE method: %s" % name)


@cli.command(name="remove-dge-method", short_help='Removes the DGE method with the given name')
@click.argument('name', metavar='<name>')
def delete_dge_method(name):
    roger.backend.dge.delete_method(db.session(), name)
    print("Deleted DGE method: %s" % name)

# TODO consume this
#getpass.getuser()