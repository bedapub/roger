import click

from roger.cli import cli
from roger.persistence import db
import roger.persistence.dge


class CommaSeparatedListOfStrings(click.Option):

    def type_cast_value(self, ctx, value):
        try:
            if not value:
                return []
            return value.split(',')
        except:
            raise click.BadParameter(value)


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
    print(roger.persistence.dge.list_methods(db.session()))


@cli.command(name="show-microarrays",
             short_help='Gives a list of available microarray platforms for a given species')
@click.argument('tax_id', metavar='<tax_id>', type=int)
def add_dataset(tax_id):
    import roger.persistence.geneanno
    from roger.logic.mart import get_annotation_service
    annotation_service = get_annotation_service()

    species_list = roger.persistence.geneanno.list_species(db.session())
    dataset_name = species_list.loc[species_list["TaxID"] == tax_id, "Version"].values[0].split(' ')[0]

    dataset = annotation_service.get_dataset(dataset_name)

    probe_attributes = [name for (name, attr) in dataset.attributes.items() if "probe" in attr.display_name]
    for probe_attribute in probe_attributes:
        print(probe_attribute)


@cli.command(name="add-ds",
             short_help='Adds a new data set to ROGER')
@click.argument('gct_file', metavar='<gct_file>', type=click.Path(exists=True))
@click.argument('tax_id', metavar='<tax_id>', type=int)
@click.option('--groups',
              cls=CommaSeparatedListOfStrings,
              help='Comma-separated list of groups - one entry for each sample')
@click.option('--pheno-from-design',
              type=click.Path(exists=True),
              help='Use given design matrix to extract grouping information for the samples')
@click.option('--microarray',
              type=click.Path(exists=True),
              help='The Ensembl BioMart name of the microarray platform used for annotating ')
def add_dataset(gct_file, tax_id, groups, pheno_from_design, microarray):
    print(gct_file)
    print(groups)
    #roger.persistence.dge.add_method(db.session(), name, description, version)
    #print("Added DGE method: %s" % name)


@cli.command(name="remove-ds",
             short_help='Removes the data set from ROGER with the given name')
@click.argument('name', metavar='<name>')
def remove_dataset(name):
    roger.persistence.dge.delete_method(db.session(), name)
    print("Deleted DGE method: %s" % name)
