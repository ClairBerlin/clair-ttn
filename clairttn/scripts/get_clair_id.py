#!/usr/bin/env python3

import click
import clairttn.ers as ers

@click.command()
@click.argument("dev-eui")
def get_device_id(dev_eui):
    print(ers.ErsDeviceUUID(bytes.fromhex(dev_eui)))
