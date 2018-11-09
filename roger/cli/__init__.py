import click
import sys
import os

from flask.cli import FlaskGroup

import roger.flask


@click.group(cls=FlaskGroup, create_app=roger.flask.create_app)
@click.option('--config', help='Pass ROGER configuration file')
def cli(config):
    """ROGER management application"""
    if config is not None:
        os.environ['ROGER_CONFIG'] = config
    if 'ROGER_CONFIG' not in os.environ or not os.environ['ROGER_CONFIG']:
        home = os.path.expanduser("~")
        os.environ['ROGER_CONFIG'] = os.path.join(home, ".roger_config.cfg")

    # Check if config file does exist
    config_file = os.environ['ROGER_CONFIG']
    if not os.path.isfile(config_file):
        print("Cannot open config file: %s" % config_file, file=sys.stderr)
        sys.exit(-1)
