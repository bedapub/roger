import click
import flask

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
    import roger.persistence.dge

    session = db.session()

    print("Parsing and annotating data ...")
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

    print("Persisting data set ...")
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
    import roger.persistence.dge

    session = db.session()

    print("Parsing and annotating data ...")
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

    print("Persisting data set ...")
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


@cli.command(name="show-exprs",
             short_help='Shows the expression matrix from a given data set')
@click.argument('dataset', metavar='<dataset_name>')
def show_exprs(dataset):
    print("Querying dataset '%s'..." % dataset)
    from roger.persistence import db
    from roger.persistence.dge import get_ds

    ds = get_ds(db.session(), dataset)
    print(ds.exprs_data)


@cli.command(name="export-exprs",
             short_help='Exports the expression matrix from a given data set')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('out_file', type=click.File('wb'))
def export_exprs(dataset, out_file):
    print("Saving expression matrix to '%s' ..." % out_file.name)
    from roger.persistence import db
    from roger.persistence.dge import get_ds
    import shutil

    ds = get_ds(db.session(), dataset)
    shutil.copy(ds.ExprsWC, out_file.name)
    print("Done")


@cli.command(name="show-feature-data",
             short_help='Shows the feature annotation data from a given data set')
@click.argument('dataset', metavar='<dataset_name>')
def show_feature_data(dataset):
    print("Querying dataset '%s'..." % dataset)
    from roger.persistence import db
    from roger.persistence.dge import get_ds

    ds = get_ds(db.session(), dataset)
    print(ds.feature_data)


@cli.command(name="export-feature-data",
             short_help='Exports the feature annotation data from a given data set')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('out_file', type=click.File('wb'))
def export_feature_data(dataset, out_file):
    print("Saving feature annotation data to '%s' ..." % out_file.name)
    from roger.persistence import db
    from roger.persistence.dge import get_ds

    ds = get_ds(db.session(), dataset)
    ds.feature_data.to_csv(out_file, sep="\t")
    print("Done")


@cli.command(name="show-pheno-data",
             short_help='Shows the pheno data from a given data set')
@click.argument('dataset', metavar='<dataset_name>')
def show_pheno_data(dataset):
    print("Querying dataset '%s'..." % dataset)
    from roger.persistence import db
    from roger.persistence.dge import get_ds

    ds = get_ds(db.session(), dataset)
    print(ds.pheno_data)


@cli.command(name="export-pheno-data",
             short_help='Exports the pheno data from a given data set')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('out_file', type=click.File('wb'))
def export_pheno_data(dataset, out_file):
    print("Saving pheno data to '%s' ..." % out_file.name)
    from roger.persistence import db
    from roger.persistence.dge import get_ds

    ds = get_ds(db.session(), dataset)
    ds.pheno_data.to_csv(out_file, sep="\t")
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
@click.option('--sample_groups',
              help='File containing a list of sample groups, separated by newline',
              type=click.Path(exists=True))
@click.option('--sample_group_levels',
              help='File containing a list of sample group levels, separated by newline',
              type=click.Path(exists=True))
@click.option('--sample_group_column',
              help='Name of column in the pheno data matrix from which ROGER should'
                   'read the sample groups')
def add_design(design_matrix,
               dataset,
               name,
               description,
               sample_groups,
               sample_group_levels,
               sample_group_column):
    name = get_or_guess_name(name, design_matrix)

    print("Adding design '%s' to data set '%s' ..." % (name, dataset))
    from roger.persistence import db
    import roger.persistence.dge

    name = roger.persistence.dge.add_design(db.session(),
                                            design_matrix,
                                            dataset,
                                            name,
                                            description,
                                            sample_groups,
                                            sample_group_levels,
                                            sample_group_column)
    print("Done - added design with name '%s'" % name)


@cli.command(name="show-design",
             short_help='Show contrast matrix')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
def show_design(design, dataset):
    print('Querying available DGE models ...')
    from roger.persistence import db
    from roger.persistence.dge import get_design

    design = get_design(db.session(), design, dataset)
    print(design.design_matrix)


@cli.command(name="export-design",
             short_help='Exports design matrix onto the disk')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('out_file', type=click.File('wb'))
def export_design(design, dataset, out_file):
    print("Saving design matrix to '%s' ..." % out_file.name)
    from roger.persistence import db
    from roger.persistence.dge import get_design

    design = get_design(db.session(), design, dataset)
    design.design_matrix.to_csv(out_file, sep="\t")
    print("Done")


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


@cli.command(name="show-contrast",
             short_help='Show contrast matrix')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
def show_contrast(contrast, design, dataset):
    print('Querying available DGE models ...')
    from roger.persistence import db
    from roger.persistence.dge import get_contrast

    contrast = get_contrast(db.session(), contrast, design, dataset)
    print(contrast.contrast_matrix)


@cli.command(name="export-contrast",
             short_help='Exports contrast matrix onto the disk')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('out_file', type=click.File('wb'))
def export_contrast(contrast, design, dataset, out_file):
    print("Exporting contrast matrix to '%s' ..." % out_file.name)
    from roger.persistence import db
    from roger.persistence.dge import get_contrast

    contrast = get_contrast(db.session(), contrast, design, dataset)
    contrast.contrast_matrix.to_csv(out_file, sep="\t")
    print("Done")


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
def run_dge_ma(contrast, design, dataset):
    print("Performing DGE algorithm ...")
    from roger.persistence import db
    import roger.logic.dge

    roger.logic.dge.run_dge(db.session(),
                            flask.current_app.config['ROGER_DATA_FOLDER'],
                            contrast,
                            design,
                            dataset,
                            roger.logic.dge.LimmaDGE())
    print("Done")


@cli.command(name="run-dge-rnaseq",
             short_help='Run differential gene expression analysis on RNAseq data')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
# TODO edgeR support only for now ...
# @click.option('--algorithm', default="edgeR", help='Used method method for normalization')
def run_dge_rnaseq(contrast, design, dataset):
    print("Performing DGE algorithm ...")
    from roger.persistence import db
    import roger.logic.dge

    roger.logic.dge.run_dge(db.session(),
                            flask.current_app.config['ROGER_DATA_FOLDER'],
                            contrast,
                            design,
                            dataset,
                            roger.logic.dge.EdgeRDGE())
    print("Done")


# -----------------
# DGE Model & Results
# -----------------

@cli.command(name="list-dge-models",
             short_help='Lists DGE models')
@click.option('--contrast', help='Show only models for the given contrast')
@click.option('--design', help='Show only models for the given design')
@click.option('--dataset', help='Show only models for the given data set')
@click.option('--method_name', help='Show only models for the given contrast')
def list_dge_models(contrast, design, dataset, method_name):
    print('Querying available DGE models ...')
    from roger.persistence import db
    import roger.persistence.dge

    print(roger.persistence.dge.list_dge_models(db.session(), contrast, design, dataset, method_name))


@cli.command(name="show-dge-table",
             short_help='Shows the DGE result table for the specified design:design:contrast combination')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('method', metavar='<dge_method_name>')
def show_dge_table(contrast, design, dataset, method):
    print('Querying available DGE models ...')
    from roger.persistence import db
    import roger.persistence.dge

    model = roger.persistence.dge.get_dge_model(db.session(), contrast, design, dataset, method)
    print(model.result_table)


@cli.command(name="export-dge-table",
             short_help='Exports DGE results from a specific experiment onto the disk')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('method', metavar='<dge_method_name>')
@click.argument('out_file', type=click.File('wb'))
def export_dge_table(contrast, design, dataset, method, out_file):
    print("Exporting DGE table to '%s' ..." % out_file.name)
    from roger.persistence import db
    from roger.util import write_df
    from roger.persistence.dge import get_dge_model

    model = get_dge_model(db.session(), contrast, design, dataset, method)
    write_df(model.result_table, out_file)
    print("Done")


@cli.command(name="remove-dge-model",
             short_help='Removes the given DGE model and its result entries')
@click.argument('contrast', metavar='<contrast>')
@click.argument('design', metavar='<design_name>')
@click.argument('dataset', metavar='<dataset_name>')
@click.argument('method', metavar='<dge_method_name>')
def remove_dge_model(contrast, design, dataset, method):
    print("Deleting DGE result from %s:%s:%s calculated with method %s" % (dataset, design, contrast, method))
    from roger.persistence import db
    from roger.persistence.dge import remove_dge_model

    remove_dge_model(db.session(), contrast, design, dataset, method)
    print("Done")
