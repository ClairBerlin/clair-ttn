#!/usr/bin/env python3

import logging

# set up debug logging to stderr
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

import click
import signal
import time
from clairttnesr.handler import Handler

signal_received = False

def handle_signal(signal_number, stack_frame):
    logging.debug("signal {} received".format(signal_number))
    global signal_received
    signal_received = True

@click.command()
@click.option('-i', '--app-id', default='clair-berlin-ers-co2', show_default=True, envvar='TTN_APP_ID')
@click.option('-k', '--access-key-file', envvar='TTN_ACCESS_KEY_FILE', required=True, type=click.File())
def main(app_id, access_key_file):
    signal.signal(signal.SIGINT, handle_signal)

    access_key = access_key_file.read().rstrip('\n')

    handler = Handler(app_id, access_key)
    handler.connect()

    while not signal_received:
        time.sleep(1)

    handler.close()
