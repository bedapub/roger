import click
import flask

import roger.logic.dge
import roger.persistence.dge
from roger.cli import cli
from roger.persistence.schema import MicroArrayType, RNASeqDataSet, RNASeqType, MicroArrayDataSet
from roger.util import get_enum_names, get_or_guess_name


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


@cli.command(name="add-ds-ma",
             short_help='Adds a new microarray data set to ROGER')
@click.argument('norm_exprs_file', metavar='<normalized_expression_data_file>', type=click.Path(exists=True))
@click.argument('tax_id', metavar='<tax_id>', type=int)
@click.argument('symbol_type', metavar='<symbol_type>')
@click.option('--pheno_file',
              help='Path to file containing pheno data / sample annotations',
              type=click.Path(exists=True))
@click.option('--name', help='A unique identifier for the data set (default: file name)')
@click.option('--normalization',
              type=click.Choice(get_enum_names(MicroArrayType)),
              help='Used method method for normalization')
@click.option('--description', help='General data set description')
@click.option('--xref', help='External (GEO) reference')
def add_ds_ma(norm_exprs_file,
              tax_id,
              symbol_type,
              pheno_file,
              name,
              normalization,
              description,
              xref):
    name = get_or_guess_name(name, norm_exprs_file)

    print("Adding microarray data set '%s' ..." % name)
    from roger.persistence import db
    import roger.logic.dge

    session = db.session()

    print("Parsing and annotating data")
    ds_prop = roger.logic.dge.create_ds(session,
                                        MicroArrayDataSet,
                                        norm_exprs_file,
                                        tax_id,
                                        symbol_type,
                                        pheno_file,
                                        name,
                                        normalization,
                                        description,
                                        xref)

    print("Parsing data set")
    roger.persistence.dge.add_ds(session,
                                 flask.current_app.config['ROGER_DATA_FOLDER'],
                                 ds_prop)
    print("Done - added data set with name '%s'" % name)


@cli.command(name="add-ds-rnaseq",
             short_help='Adds a new RNAseq data set to ROGER')
@click.argument('exprs_file', metavar='<expression_data_file>', type=click.Path(exists=True))
@click.argument('tax_id', metavar='<tax_id>', type=int)
@click.argument('symbol_type', metavar='<symbol_type>')
@click.option('--pheno_file',
              help='Path to file containing pheno data / sample annotations',
              type=click.Path(exists=True))
@click.option('--name', help='A unique identifier for the data set (default: file name)')
@click.option('--normalization',
              type=click.Choice(get_enum_names(RNASeqType)),
              help='Used method method for normalization')
@click.option('--description', help='General data set description')
@click.option('--xref', help='External (GEO) reference')
def add_ds_rnaseq(exprs_file,
                  tax_id,
                  symbol_type,
                  pheno_file,
                  name,
                  normalization,
                  description,
                  xref):
    name = get_or_guess_name(name, exprs_file)

    print("Adding RNAseq data set '%s' ..." % name)
    from roger.persistence import db
    import roger.logic.dge

    session = db.session()

    print("Parsing and annotating data")
    ds_prop = roger.logic.dge.create_ds(session,
                                        RNASeqDataSet,
                                        exprs_file,
                                        tax_id,
                                        symbol_type,
                                        pheno_file,
                                        name,
                                        normalization,
                                        description,
                                        xref)

    print("Parsing data set")
    roger.persistence.dge.add_ds(session,
                                 flask.current_app.config['ROGER_DATA_FOLDER'],
                                 ds_prop)
    print("Done - added data set with name '%s'" % name)


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
# Design Matrix
# -----------------


@cli.command(name="list-design",
             short_help='Lists available designs')
@click.option('--dataset', help='Show only designs for the given data set')
def list_design(dataset):
    print('Querying available data sets ...')
    from roger.persistence import db
    import roger.persistence.dge

    print(roger.persistence.dge.list_design(db.session()), dataset)


@cli.command(name="add-design",
             short_help='Adds a new experiment design to a data set')
@click.argument('design_matrix', metavar='<design_matrix>', type=click.Path(exists=True))
@click.argument('dataset', metavar='<dataset>')
@click.option('--name', help='A unique identifier for the design (default: file name)')
@click.option('--description', help='General design description')
def add_design(design_matrix,
               dataset,
               name,
               description):
    name = get_or_guess_name(name, design_matrix)

    print("Adding design '%s' to data set '%s' ..." % (name, dataset))
    from roger.persistence import db
    import roger.persistence.dge

    name = roger.persistence.dge.add_design(db.session(),
                                            design_matrix,
                                            dataset,
                                            name,
                                            description)
    print("Done - added design with name '%s'" % name)


@cli.command(name="remove-design",
             short_help='Removes the given design')
@click.argument('design_name', metavar='<design_name>')
@click.argument('dataset_name', metavar='<dataset_name>')
def remove_design(design_name, dataset_name):
    print("Deleting design '%s' from data set '%s' ..." % (dataset_name, design_name))
    from roger.persistence import db
    import roger.persistence.dge

    roger.persistence.dge.remove_design(db.session(), design_name, dataset_name)
    print("Done")


# -----------------
# Contrast Matrix
# -----------------


@cli.command(name="list-contrast",
             short_help='Lists available contrasts')
@click.option('--design', help='Show only contrasts for the given design')
@click.option('--dataset', help='Show only contrasts for the given data set')
def list_contrast(design, dataset):
    print('Querying available contrasts ...')
    from roger.persistence import db
    import roger.persistence.dge

    print(roger.persistence.dge.list_contrast(db.session(), design, dataset))


@cli.command(name="add-contrast",
             short_help='Adds a new experiment contrast to a design')
@click.argument('contrast_matrix', metavar='<contrast_matrix>', type=click.Path(exists=True))
@click.argument('design', metavar='<design>')
@click.argument('dataset', metavar='<dataset>')
@click.option('--name', help='A unique identifier for the design (default: file name)')
@click.option('--description', help='General design description')
def add_contrast(contrast_matrix,
                 design,
                 dataset,
                 name,
                 description):
    name = get_or_guess_name(name, contrast_matrix)

    print("Adding contrast '%s' to data set '%s' ..." % (name, dataset))
    from roger.persistence import db
    import roger.persistence.dge

    name = roger.persistence.dge.add_contrast(db.session(),
                                              contrast_matrix,
                                              design,
                                              dataset,
                                              name,
                                              description)
    print("Done - added contrast with name '%s'" % name)


@cli.command(name="remove-contrast",
             short_help='Removes the given contrast')
@click.argument('contrast_name', metavar='<contrast_name>')
@click.argument('design_name', metavar='<design_name>')
@click.argument('dataset_name', metavar='<dataset_name>')
def remove_contrast(contrast_name, design_name, dataset_name):
    print("Deleting contrast '%s' of design '%s' ..." % (contrast_name, design_name))
    from roger.persistence import db
    import roger.persistence.dge

    roger.persistence.dge.remove_contrast(db.session(), contrast_name, design_name, dataset_name)
    print("Done")


# -----------------
# DGE & executions
# -----------------


@cli.command(name="run-dge-ma",
             short_help='Run differential gene expression analysis on microarray data')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
# TODO limma support only for now ...
# @click.option('--algorithm', default="limma", help='Used method method for normalization')
def run_dge_ma(contrast, design, dataset, algorithm="limma"):
    print("Performing DGE algorithm '%s' ..." % algorithm)
    from roger.persistence import db
    import roger.logic.dge

    roger.logic.dge.run_dge(db.session(),
                            flask.current_app.config['ROGER_DATA_FOLDER'],
                            contrast,
                            design,
                            dataset,
                            roger.logic.dge.perform_limma,
                            algorithm)
    print("Done")


@cli.command(name="run-dge-rnaseq",
             short_help='Run differential gene expression analysis on RNAseq data')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
# TODO edgeR support only for now ...
# @click.option('--algorithm', default="edgeR", help='Used method method for normalization')
def run_dge_rnaseq(contrast, design, dataset, algorithm="edgeR"):
    print("Performing DGE algorithm '%s' ..." % algorithm)
    from roger.persistence import db
    import roger.logic.dge

    roger.logic.dge.run_dge(db.session(),
                            flask.current_app.config['ROGER_DATA_FOLDER'],
                            contrast,
                            design,
                            dataset,
                            roger.logic.dge.perform_edger,
                            algorithm)
    print("Done")
