#!/usr/bin/env python3

import logging

# set up debug logging to stderr
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

import click
import signal
import time
import clairttn.handler as clhandler

signal_received = False

def handle_signal(signal_number, stack_frame):
    logging.debug("signal {} received".format(signal_number))
    global signal_received
    signal_received = True


HANDLERS = [
    'clairchen-forward',
    'ers-forward',
    'ers-configure'
]


@click.command()
@click.option('-i', '--app-id', default='clair-berlin-ers-co2', show_default=True, envvar='CLAIR_TTN_APP_ID')
@click.option('-k', '--access-key-file', envvar='CLAIR_TTN_ACCESS_KEY_FILE', required=True, type=click.File())
@click.option('-m', '--mode', type=click.Choice(HANDLERS), required=True)
@click.option('-r', '--api-root', envvar="CLAIR_API_ROOT", default='http://localhost:8888/api/data/v1/')
def main(app_id, access_key_file, mode, api_root):
    signal.signal(signal.SIGINT, handle_signal)

    access_key = access_key_file.read().rstrip('\n')

    if mode == 'clairchen-forward':
        handler = clhandler.ClairchenForwardingHandler(app_id, access_key, api_root)
    elif mode == 'ers-forward':
        handler = clhandler.ErsForwardingHandler(app_id, access_key, api_root)
    elif mode == 'ers-configure':
        handler = clhandler.ErsConfigurationHandler(app_id, access_key)
    else:
        # never reached thanks to click's option parsing
        click.echo("invalid mode: {}".format(mode))
        return

    handler.connect()

    while not signal_received:
        time.sleep(1)

    handler.close()
