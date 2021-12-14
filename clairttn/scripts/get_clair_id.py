#!/usr/bin/env python3

import click
import clairttn.ers as ers


@click.command()
@click.argument("dev-eui")
def get_device_id(dev_eui):
    """Convert a device EUI of an Elsys ERS sensor node to the corresponding managair device id.

    \b
    DEV_EUI is the LoraWAN device EUI.
    """

    print(ers.ErsDeviceUUID(bytes.fromhex(dev_eui)))
