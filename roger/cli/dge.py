import click
import flask
import os

from roger.cli import cli
from roger.persistence import db
import roger.persistence.dge
import roger.logic.geneanno
import roger.logic.dge
import roger.persistence.geneanno
import roger.util


# ---------------
# DGE methods
# ---------------


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


# ---------------
# Datasets
# ---------------


@cli.command(name="list-ds",
             short_help='Lists available datasets')
def list_ds():
    print(roger.persistence.dge.list_ds(db.session()))


@cli.command(name="show-symbol-types",
             short_help='Shows a list of supported symbol types')
@click.argument('tax_id', metavar='<tax_id>', type=int)
def show_symbol_types(tax_id):
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


@cli.command(name="add-ds",
             short_help='Adds a new data set to ROGER')
@click.argument('dataset_file', metavar='<dataset_file>', type=click.Path(exists=True))
@click.argument('design_file', metavar='<groups_file>', type=click.Path(exists=True))
@click.argument('tax_id', metavar='<tax_id>', type=int)
@click.argument('symbol_type', metavar='<symbol_type>')
@click.option('--exprs-type',
              type=click.Choice(["RMA", "MAS5"]),
              default="RMA",
              help='Type of expression data: Can be "RMA" or "MAS5"')
@click.option('--name', help='A unique identifier for the data set (will use file name as default)')
@click.option('--description', help='Dataset descriptioon')
@click.option('--xref', help='External (GEO) reference')
def add_ds(dataset_file, design_file, tax_id, symbol_type, exprs_type, name, description, xref):
    roger.logic.dge.add_ds(db.session(),
                           flask.current_app.config['ROGER_DATA_FOLDER'],
                           dataset_file,
                           design_file,
                           tax_id,
                           symbol_type,
                           exprs_type,
                           name,
                           description,
                           xref)
    print("Done")


@cli.command(name="remove-ds",
             short_help='Removes the Differential Gene Expression  method with the given name')
@click.argument('name', metavar='<name>')
def remove_ds(name):
    ds_entiry = roger.persistence.dge.get_ds(db.session(), name)
    os.remove(ds_entiry.PhenoWC)
    os.remove(ds_entiry.ExprsWC)
    os.remove(ds_entiry.NormalizedExprsWC)
    roger.persistence.dge.delete_method(db.session(), name)
    print("Deleted data set: %s" % name)


# ---------------
# DGE & executions
# ---------------


@cli.command(name="list-ds",
             short_help='Lists available datasets')
def list_dge_models():
    print(roger.persistence.dge.list_ds(db.session()))


@cli.command(name="run-dge",
             short_help='Executes differential gene expression analysis for the given algorithm')
@click.argument('algorithm', metavar='(limma|edgeR)', type=click.Choice(['limma', 'edgeR']))
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('design', metavar='<design_file>', type=click.Path(exists=True))
@click.argument('contrast', metavar='<contrast>', type=click.Path(exists=True))
@click.option('--design_name', help='Name of the design (must be unique within each data set / study)')
def run_dge(algorithm, dataset, design, contrast, design_name):
    roger.logic.dge.run_dge(db.session(),
                            flask.current_app.config['ROGER_DATA_FOLDER'],
                            algorithm,
                            dataset,
                            design,
                            contrast,
                            design_name)
    print("Done")
