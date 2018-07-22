import click
import flask

from roger.cli import cli
from roger.persistence.schema import MicroArrayType
from roger.util import get_enum_names

# ---------------
# DGE methods
# ---------------


@cli.command(name="list-dge-methods",
             short_help='Lists all Differential Gene Expression methods utilized in ROGER studies')
def list_dge_methods():
    print('Querying available DGE methods ...')
    from roger.persistence import db
    import roger.persistence.dge

    print(roger.persistence.dge.list_methods(db.session()))


# TODO: No method customization for now
# @cli.command(name="add-dge-method",
#              short_help='Adds a new Differential Gene Expression method to the database')
# @click.argument('name', metavar='<name>')
# @click.argument('description', metavar='<description>')
# @click.argument('version', metavar='<version>')
# def add_dge_method(name, description, version):
#     print("Adding DGE method '%s' ..." % name)
#     from roger.persistence import db
#     import roger.persistence.dge
#
#     roger.persistence.dge.add_method(db.session(), name, description, version)
#     print("Done")


# TODO: No method customization for now
# @cli.command(name="remove-dge-method",
#              short_help='Removes the Differential Gene Expression method with the given name')
# @click.argument('name', metavar='<name>')
# def remove_dge_method(name):
#     print("Deleting DGE method '%s' ..." % name)
#     from roger.persistence import db
#     import roger.persistence.dge
#
#     roger.persistence.dge.delete_method(db.session(), name)
#     print("Done")


# ---------------
# Datasets
# ---------------


@cli.command(name="list-ds",
             short_help='Lists available datasets')
def list_ds():
    print('Querying available data sets ...')
    from roger.persistence import db
    import roger.persistence.dge

    print(roger.persistence.dge.list_ds(db.session()))


@cli.command(name="show-symbol-types",
             short_help='Shows a list of supported symbol types')
@click.argument('tax_id', metavar='<tax_id>', type=int)
def show_symbol_types(tax_id):
    print('Querying available symbol types ...')

    from roger.persistence import db
    import roger.logic.geneanno
    import roger.util

    dataset = roger.logic.geneanno.get_dataset_of(db.session(), tax_id)

    common_identifiers = [x.value for x in roger.logic.geneanno.CommonGeneIdentifier]

    attributes = dataset.attributes
    gene_attributes = attributes.loc[attributes['name'].isin(common_identifiers),
                                     ["name", "display_name"]]
    probe_attributes = attributes.loc[attributes.apply(lambda x: "probe" in x["display_name"], axis=1),
                                      ["name", "display_name"]]
    print("Gene identifiers:")
    print(gene_attributes.to_string(index=False))

    print("Microarray probes:")
    print(probe_attributes.to_string(index=False))


@cli.command(name="add-ma-ds",
             short_help='Adds a new microarray data set to ROGER')
@click.argument('norm_exprs_file', metavar='<normalized_expression_data_file>', type=click.Path(exists=True))
@click.argument('tax_id', metavar='<tax_id>', type=int)
@click.argument('symbol_type', metavar='<symbol_type>')
@click.option('--exprs_file',
              help='Path to file containing raw expresion data',
              type=click.Path(exists=True))
@click.option('--pheno_file',
              help='Path to file containing pheno data / sample annotations',
              type=click.Path(exists=True))
@click.option('--name', help='A unique identifier for the data set '
                             '(will use the normalized expression data file name as default)')
@click.option('--normalization',
              type=click.Choice(get_enum_names(MicroArrayType)),
              default=MicroArrayType.RMA.name,
              help='Used method method for normalization')
@click.option('--description', help='Dataset descriptioon')
@click.option('--xref', help='External (GEO) reference')
def add_ma_data(norm_exprs_file,
                tax_id,
                symbol_type,
                exprs_file,
                pheno_file,
                name,
                normalization,
                description,
                xref):
    print("Adding microarray data set '%s' ..." % name)
    from roger.persistence import db
    import roger.logic.dge

    roger.logic.dge.add_ma_ds(db.session(),
                              flask.current_app.config['ROGER_DATA_FOLDER'],
                              norm_exprs_file,
                              tax_id,
                              symbol_type,
                              exprs_file,
                              pheno_file,
                              name,
                              normalization,
                              description,
                              xref)
    print("Done")


# TODO remove directories
@cli.command(name="remove-ds",
             short_help='Removes the Differential Gene Expression  method with the given name')
@click.argument('name', metavar='<name>')
def remove_ds(name):
    print("Deleting data set '%s' ..." % name)
    from roger.persistence import db
    import roger.persistence.dge

    roger.persistence.dge.delete_ds(db.session(), name)
    print("Done")


# -----------------
# DGE & executions
# -----------------


@cli.command(name="run-dge",
             short_help='Executes differential gene expression analysis for the given algorithm')
@click.argument('algorithm', metavar='(limma|edgeR)', type=click.Choice(['limma', 'edgeR']))
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('design', metavar='<design_file>', type=click.Path(exists=True))
@click.argument('contrast', metavar='<contrast>', type=click.Path(exists=True))
@click.option('--design_name', help='Name of the design (must be unique within each data set / study)')
def run_dge(algorithm, dataset, design, contrast, design_name):
    print("Performing DGE algorithm '%s' ..." % algorithm)
    from roger.persistence import db
    import roger.logic.dge

    roger.logic.dge.run_dge(db.session(),
                            flask.current_app.config['ROGER_DATA_FOLDER'],
                            algorithm,
                            dataset,
                            design,
                            contrast,
                            design_name)
    print("Done")
