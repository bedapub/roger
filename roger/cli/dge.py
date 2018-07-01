import click

from roger.cli import cli
from roger.persistence import db
import roger.persistence.dge


@cli.command(name="list-dge-methods",
             short_help='Lists all Differential Gene Expression methods utilized in ROGER studies')
def list_dge_methods():
    print(roger.persistence.dge.list_methods(db.session()))


@cli.command(name="add-dge-method",
             short_help='Adds a new Differential Gene Expression method to the database')
@click.argument('name', metavar='<name>')
@click.argument('description', metavar='<description>')
@click.argument('version', metavar='<version>')
def add_dge_method(name, description, version):
    roger.persistence.dge.add_method(db.session(), name, description, version)
    print("Added DGE method: %s" % name)


@cli.command(name="remove-dge-method",
             short_help='Removes the Differential Gene Expression  method with the given name')
@click.argument('name', metavar='<name>')
def remove_dge_method(name):
    roger.persistence.dge.delete_method(db.session(), name)
    print("Deleted DGE method: %s" % name)
