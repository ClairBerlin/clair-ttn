#!/usr/bin/env python3

import logging

# set up debug logging to stderr
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

import click
import signal
import time
import clairttn.node_handler as clhandler
import clairttn.ttn_handler as ttnhandler

signal_received = False


def handle_signal(signal_number, _stack_frame):
    logging.debug("signal {} received".format(signal_number))
    global signal_received
    signal_received = True


HANDLERS = ["clairchen-forward", "ers-forward", "ers-configure", "oy1012-forward"]

STACKS = ["ttn-v2", "ttn-v3"]


@click.command()
@click.option(
    "-i",
    "--app-id",
    default="clair-berlin-ers-co2",
    show_default=True,
    envvar="CLAIR_TTN_APP_ID",
)
@click.option(
    "-k",
    "--access-key-file",
    envvar="CLAIR_TTN_ACCESS_KEY_FILE",
    required=True,
    type=click.File(),
)
@click.option(
    "-m", "--mode", type=click.Choice(HANDLERS), envvar="CLAIR_MODE", required=True
)
@click.option(
    "-r",
    "--api-root",
    envvar="CLAIR_API_ROOT",
    default="http://localhost:8888/ingest/v1/",
    show_default=True,
)
@click.option(
    "-s",
    "--stack",
    type=click.Choice(STACKS),
    envvar="CLAIR_TTN_STACK",
    default="ttn-v2",
)
def main(app_id, access_key_file, mode, api_root, stack):
    """Clair TTN application that can be run in one of the following modes:

    \b
    * Clairchen forwarding
    * ERS forwarding
    * ERS configuration
    * OY1012 forwarding
    """
    signal.signal(signal.SIGINT, handle_signal)

    access_key = access_key_file.read().rstrip("\n")

    # Select the appropriate payload handler for the configured type of node.
    if mode == "clairchen-forward":
        node_handler = clhandler.ClairchenForwardingHandler(api_root)
    elif mode == "ers-forward":
        node_handler = clhandler.ErsForwardingHandler(api_root)
    elif mode == "ers-configure":
        node_handler = clhandler.ErsConfigurationHandler(api_root)
    elif mode == "oy1012-forward":
        node_handler = clhandler.Oy1012ForwardingHandler(api_root)
    else:
        # never reached thanks to click's option parsing
        click.echo("invalid mode: {}".format(mode))
        return

    if stack == "ttn-v2":
        ttn_handler = ttnhandler.TtnV2Handler(app_id, access_key, node_handler)
    elif stack == "ttn-v3":
        ttn_handler = ttnhandler.TtnV3Handler(app_id, access_key, node_handler)
    else:
        # never reached thanks to click's option parsing
        click.echo("invalid TTN stack: {}".format(stack))
        return

    ttn_handler.connect()

    while not signal_received:
        time.sleep(1)

    ttn_handler.disconnect_and_close()
