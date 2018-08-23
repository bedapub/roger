import click
import flask

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

    roger.persistence.gse.add_gmt(db.session(), flask.current_app.config['ROGER_DATA_FOLDER'], category_name, gmt_file,
                                  tax_id)
    print("Done")


@cli.command(name="remove-gmt", short_help='Removes all gene sets associated with the given gene sete category')
@click.argument('category_name', metavar='<category_name>')
def remove_gmt(category_name):
    print("Deleting gene set category '%s' ..." % category_name)
    from roger.persistence import db
    import roger.persistence.gse

    roger.persistence.gse.delete_gmt(db.session(), category_name)
    print("Done")


# -----------------
# GSE & execution
# -----------------


@cli.command(name="run-gse",
             short_help='Run Gene Set Enrichment analysis')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('dge_method', metavar='<dge_method>')
@click.option('--gene_set_category_filters',
              help='File containing a list of gene set categories used for the GSE analysis, separated by newline',
              type=click.Path(exists=True))
# @click.option('--algorithm', default="camera", help='Used method method for normalization')
def run_gse(contrast, design, dataset, dge_method, gene_set_category_filters):
    print("Performing GSE algorithm ...")
    from roger.persistence import db
    import roger.persistence.dge
    import roger.persistence.gse
    import roger.logic.dge
    import roger.logic.gse

    session = db.session()

    dge_model = roger.persistence.dge.get_dge_model(session, contrast, design, dataset, dge_method)

    # TODO CAMERA support only for now ... (which is in [0] always)
    camera_algorithm = roger.logic.dge.get_algorithm(dge_model.Method.Name).gse_methods[0]()

    gse_table = roger.logic.gse.perform_gse(session,
                                            dge_model,
                                            camera_algorithm,
                                            gene_set_category_filters)

    print("Persisting data into database ...")
    roger.persistence.gse.create_gse_result(session, gse_table)

    print("Done")


@cli.command(name="list-gse-tables",
             short_help='Lists available GSE results')
@click.option('--contrast', help='Show only result overviews for the given contrast')
@click.option('--design', help='Show only result overviews for the given design')
@click.option('--dataset', help='Show only result overviews for the given data set')
@click.option('--dge_method', help='Show only result overviews for the given DGE method')
@click.option('--gse_method', help='Show only result overviews for the given GSE method')
def list_gse_tables(contrast, design, dataset, dge_method, gse_method):
    print('Querying available DGE models ...')
    from roger.persistence import db
    import roger.persistence.gse

    print(roger.persistence.gse.list_gse_tables(db.session(), contrast, design, dataset, dge_method, gse_method))


@cli.command(name="show-gse-table",
             short_help='Shows the GSE result table for the specified design:design:contrast:dge_method combination')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('dge_method', metavar='<dge_method_name>')
@click.argument('gse_method', metavar='<gse_method_name>')
def show_gse_table(contrast, design, dataset, dge_method, gse_method):
    print('Querying GSE table ...')
    from roger.persistence import db
    import roger.persistence.gse

    result_table = roger.persistence.gse.get_gse_table(db.session(),
                                                       contrast, design, dataset,
                                                       dge_method, gse_method)
    print(result_table)


@cli.command(name="export-gse-table",
             short_help='Exports DGE results from a specific experiment onto the disk')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('dge_method', metavar='<dge_method_name>')
@click.argument('gse_method', metavar='<gse_method_name>')
@click.argument('out_file', type=click.File('wb'))
def export_gse_table(contrast, design, dataset, dge_method, gse_method, out_file):
    print("Exporting GSE table to '%s' ..." % out_file.name)
    from roger.persistence import db
    from roger.util import write_df
    from roger.persistence.gse import get_gse_table

    result_table = get_gse_table(db.session(), contrast, design, dataset, dge_method, gse_method)
    write_df(result_table, out_file)
    print("Done")


@cli.command(name="remove-gse-table",
             short_help='Removes the given GSE result table for the specific experiment')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('dge_method', metavar='<dge_method_name>')
@click.argument('gse_method', metavar='<gse_method_name>')
def remove_gse_table(contrast, design, dataset, dge_method, gse_method):
    print("Deleting GSE result from %s:%s:%s:%s:%s"
          % (dataset, design, contrast, dge_method, gse_method))
    from roger.persistence import db
    from roger.persistence.gse import remove_gse_table

    remove_gse_table(db.session(), contrast, design, dataset, dge_method, gse_method)
    print("Done")
