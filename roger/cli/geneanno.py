import click

from roger.cli import cli


@cli.command(name="list-species", short_help='Lists all species with imported gene annotation data')
def list_species():
    """Used to retrieve a table of species whose gene annotation data has been imported into the database instance.
    """
    print('Querying available species ...')
    from roger.persistence import db
    import roger.persistence.geneanno

    print(roger.persistence.geneanno.list_species(db.session()))


@cli.command(name="add-species", short_help='Import gene annotation data from Ensembl BioMart dataset')
@click.argument('dataset', metavar='<dataset>')
@click.argument('tax_id', type=int, metavar='<tax_id>')
def add_species(dataset, tax_id):
    """Used to import gene annotation data from Ensembl from a specific dataset / species

    Example:
        roger import-geneanno rnorvegicus_gene_ensembl 10116
    """
    print("Importing gene annotation for species %s ..." % tax_id)

    from roger.persistence import db
    import roger.persistence.geneanno

    roger.persistence.geneanno.add_species(db.session(), dataset, tax_id)
    print("Done")


@cli.command(name="remove-species", short_help='Removes gene annotation data from the database instance')
@click.argument('tax_id', type=int, metavar='<tax_id>')
def remove_gene_anno(tax_id):
    """Used to delete imported gene annotation data from the database
    """
    print("Deleted gene annotation for species %s" % tax_id)
    from roger.persistence import db
    import roger.persistence.geneanno

    roger.persistence.geneanno.remove_species(db.session(), tax_id)
    print("Done")


@cli.command(name="init", short_help='Initialize new ROGER instance')
def init_database():
    """Initializes the database with human gene annotation and default DGE / GSE methods
    """
    print("Initializing database ...")

    from roger.persistence import db
    import roger.persistence.geneanno
    import roger.persistence.dge
    #import roger.persistence.gse

    print("Adding human gene annotation ...")
    roger.persistence.geneanno.init(db)
    # Add standard DGE methods

    print("Adding standard DGE and GSE methods ...")
    roger.persistence.dge.add_method(db.session(), "limma", "limma")
    roger.persistence.dge.add_method(db.session(), "edgeR", "edgeR")

    print("Done")
