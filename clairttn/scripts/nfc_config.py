#!/usr/bin/env python3

import click
import pyqrcode


def _generate_nfc_config(join_eui, app_key):
    nfc_config = """\
AppEui:{}
AppKey:{}
Ota:true
Ack:false
SplPer:356
Co2Per:1
TempPer:0
SendPer:3
VddPer:0
QSize:5
QOffset:false
QPurge:true""".format(
        join_eui, app_key
    )

    return nfc_config


def _generate_qr_png(nfc_config, fila_name):
    config_code = pyqrcode.create(nfc_config)
    config_code.png(fila_name, scale=4)


@click.command()
@click.argument("join-eui")
@click.argument("dev-eui")
@click.argument("app-key")
def generate_nfc_config(join_eui, dev_eui, app_key):
    """Create NFC config files for Elsys ERS CO2 sensors..

    \b
    APP_EUI is the TTN application EUI.
    DEV_EUI is the TTN device EUI.
    APP_KEY is the TTN's app_key root key.
    """

    nfc_config = _generate_nfc_config(join_eui, app_key)

    with open("{}-nfc-config.txt".format(dev_eui), "w") as fd:
        fd.write(nfc_config)

    _generate_qr_png(nfc_config, "{}-nfc-config.png".format(dev_eui))
