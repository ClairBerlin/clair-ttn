#!/usr/bin/env python3

import click
import ttn
import sys
import clairttn.ers as ers
import pyqrcode


def _get_ttn_device(ttn_app_id, access_key, device_eui):
    device_id = ers.ErsDeviceUUID(bytes.fromhex(device_eui))
    applicationClient = ttn.HandlerClient(ttn_app_id, access_key).application()
    return applicationClient.device(str(device_id))


def _generate_nfc_config(ttn_device):
    app_eui = ttn_device.lorawan_device.app_eui.hex()
    app_key = ttn_device.lorawan_device.app_key.hex().upper()

    nfc_config = """\
AppEui:{}
Ota:true
Ack:false
AppKey:{}
SplPer:356
Co2Per:1
TempPer:0
SendPer:3
VddPer:0
QSize:5
QOffset:false
QPurge:true""".format(app_eui, app_key)

    return nfc_config


def _generate_qr_png(nfc_config, fila_name):
    config_code = pyqrcode.create(nfc_config)
    config_code.png(fila_name, scale=4)


@click.command()
@click.option('-i', '--ttn-app-id', required=True)
@click.option('-k', '--access-key-file', required=True, type=click.File())
@click.argument("device-eui")
def generate_nfc_config(ttn_app_id, access_key_file, device_eui):
    """Create NFC config files for a device registered in the TTN.

    \b
    DEVICE_EUI is the TTN device EUI.
    """
    access_key = access_key_file.read().rstrip('\n')

    try:
        ttn_device = _get_ttn_device(ttn_app_id, access_key, device_eui)
    except RuntimeError:
        print("device {} not found".format(device_eui))
        sys.exit(1)

    nfc_config = _generate_nfc_config(ttn_device)

    _generate_qr_png(nfc_config, "{}-nfc-config.png".format(device_eui))
