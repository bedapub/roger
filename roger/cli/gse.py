import click

from roger.cli import cli


@cli.command(name="list-gse-methods", short_help='Lists all Gene Set Enrichment methods utilized in ROGER studies')
def list_gse_methods():
    print('Querying available GSE methods ...')
    from roger.persistence import db
    import roger.persistence.gse

    print(roger.persistence.gse.list_methods(db.session()))
    print("Done")


# TODO: No method customization for now
# @cli.command(name="add-gse-method", short_help='Adds a new Gene Set Enrichment method to the database')
# @click.argument('name', metavar='<name>')
# @click.argument('description', metavar='<description>')
# @click.argument('version', metavar='<version>')
# def add_gse_method(name, description, version):
#     print("Adding GSE method '%s' ..." % name)
#     from roger.persistence import db
#     import roger.persistence.gse
#
#     roger.persistence.gse.add_method(db.session(), name, description, version)
#     print("Done")

# TODO: No method customization for now
# @cli.command(name="remove-gse-method", short_help='Removes the Gene Set Enrichment method with the given name')
# @click.argument('name', metavar='<name>')
# def remove_gse_method(name):
#     print("Deleting GSE method '%s' ..." % name)
#     from roger.persistence import db
#     import roger.persistence.gse
#
#     roger.persistence.gse.delete_method(db.session(), name)
#     print("Done")


@cli.command(name="list-gmt", short_help='Lists all gene set categories and their number of gene sets')
def list_gmt():
    print('Querying available GSE methods ...')
    from roger.persistence import db
    import roger.persistence.gse

    print(roger.persistence.gse.list_gmt(db.session()))


@cli.command(name="add-gmt", short_help='Adds a GMT file into the ROGER instance')
@click.argument('category_name', metavar='<category_name>')
@click.argument('gmt_file', metavar='<gmt_file>')
@click.argument('tax_id', metavar='<tax_id>')
def add_gmt(category_name, gmt_file, tax_id):
    print("Importing gene sets from GMT file '%s' ..." % gmt_file)
    from roger.persistence import db
    import roger.persistence.gse

    roger.persistence.gse.add_gmt(db.session(), category_name, gmt_file, tax_id)
    print("Done")


@cli.command(name="remove-gmt", short_help='Removes all gene sets associated with the given gene sete category')
@click.argument('category_name', metavar='<category_name>')
def remove_gmt(category_name):
    print("Deleting gene set category '%s' ..." % category_name)
    from roger.persistence import db
    import roger.persistence.gse

    roger.persistence.gse.delete_gmt(db.session(), category_name)
    print("Done")
