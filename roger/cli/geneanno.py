import click
import sys

from roger.cli import cli
from roger.persistence import db
import roger.persistence.geneanno


@cli.command(name="list-species", short_help='Lists all species with imported gene annotation data')
def list_species():
    """Used to retrieve a table of species whose gene annotation data has been imported into the database instance.
    """
    print(roger.persistence.geneanno.list_species(db.session()))


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
    roger.persistence.geneanno.add_species(db.session(), dataset, tax_id)
    print("Done")


@cli.command(name="remove-species", short_help='Removes gene annotation data from the database instance')
@click.argument('tax_id', type=int, metavar='<tax_id>')
def remove_gene_anno(tax_id):
    """Used to delete imported gene annotation data from the database
    """
    roger.persistence.geneanno.remove_species(db.session(), tax_id)
    print("Deleted gene annotation for species %s" % tax_id)


@cli.command(name="init-db", short_help='Initialize new ROGER instance')
def init_database():
    sys.stdout.write("Initializing database with human gene annotation data ...")
    sys.stdout.flush()
    roger.persistence.geneanno.init(db)
    print("Done")
