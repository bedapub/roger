import click

import roger.cli
import roger.cli.geneanno
import roger.cli.dge
import roger.cli.gse
from roger.exception import ROGERUsageError


def entry_point():
    try:
        roger.cli.cli()
    except ROGERUsageError as e:
        click.echo(e.message, err=True)
