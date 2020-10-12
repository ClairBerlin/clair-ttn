#!/usr/bin/env python3

import logging

# set up debug logging to stderr
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

import click
import signal
import time
import clairttn.handler as handler

signal_received = False

def handle_signal(signal_number, stack_frame):
    logging.debug("signal {} received".format(signal_number))
    global signal_received
    signal_received = True


HANDLERS = {
    'clairchen-forward': handler.ClairchenForwardingHandler,
    'ers-forward': handler.ErsForwardingHandler,
    'ers-configure': handler.ErsConfigurationHandler,
}


@click.command()
@click.option('-i', '--app-id', default='clair-berlin-ers-co2', show_default=True, envvar='TTN_APP_ID')
@click.option('-k', '--access-key-file', envvar='TTN_ACCESS_KEY_FILE', required=True, type=click.File())
@click.option('-m', '--mode', type=click.Choice(HANDLERS.keys()), required=True)
def main(app_id, access_key_file, mode):
    signal.signal(signal.SIGINT, handle_signal)

    access_key = access_key_file.read().rstrip('\n')
    
    handlerClass = HANDLERS[mode]
    handler = handlerClass(app_id, access_key)

    handler.connect()

    while not signal_received:
        time.sleep(1)

    handler.close()
