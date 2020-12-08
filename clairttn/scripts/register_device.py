#!/usr/bin/env python3

import click
import ttn
import clairttn.ers as ers
import os
import sys
import binascii
import requests
import jsonapi_requests as jarequests
import json
import getpass


def _create_ttn_device(device_eui, app_eui):
    application_key = binascii.b2a_hex(os.urandom(16)).upper()
    ttn_device = {
        "appEui": app_eui,
        "devEui": device_eui,
        "appKey": application_key
    }
    return ttn_device


@click.command()
@click.argument("app-id")
@click.argument("access-key-file", type=click.File())
@click.argument("app-eui")
@click.argument("device-eui", nargs=-1)
def register_device_in_ttn(app_id, access_key_file, app_eui, device_eui):
    """Register Clair TTN nodes in the TTN.

    \b
    APP_ID is the TTN application id.
    ACCESS_KEY_FILE is the file that contains the access key of the TTN application.
    APP_EUI is the TTN app EUI.
    DEVICE_EUI is the TTN device EUI.
    """

    access_key = access_key_file.read().rstrip('\n')
    application_client = ttn.HandlerClient(app_id, access_key).application()

    for dev_eui in device_eui:
        device_id = str(ers.ErsDeviceUUID(bytes.fromhex(dev_eui)))
        ttn_device = _create_ttn_device(dev_eui, app_eui)

        application_client.register_device(device_id, ttn_device)


class _TokenAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = "Token {}".format(self.token)
        return r


def _login(api_root):
    login_endpoint = jarequests.Api.config({ 'API_ROOT': api_root }).endpoint('auth/login')

    username = input("Username: ")
    password = getpass.getpass()

    login_object = jarequests.JsonApiObject(
        type = 'LoginView',
        attributes = {
            "username": username,
            "password": password
        })

    try:
        r = login_endpoint.post(object=login_object)
    except jarequests.request_factory.ApiClientError as e:
        error_object = json.loads(e.content)
        print("login failed: {}".format(error_object['errors'][0]['detail']))
        sys.exit(1)

    return r.data.attributes['key']


def _create_node(api_root, key, device_eui, alias_prefix, protocol_id, model_id, owner_id):
    api = jarequests.Api.config({
        'API_ROOT': api_root,
        'AUTH': _TokenAuth(key)
    })

    nodes_endpoint = api.endpoint('nodes')

    device_id = str(ers.ErsDeviceUUID(bytes.fromhex(device_eui)))

    node_object = jarequests.JsonApiObject(
        type = 'Node',
        id = device_id,
        attributes = {
            "eui64": device_eui,
            "alias": "{}{}".format(alias_prefix, device_eui)
        },
        relationships = {
            "protocol": { "data": { "type": "Protocol", "id": protocol_id } },
            "model": { "data": { "type": "Model", "id": model_id } },
            "owner": { "data": { "type": "Organization", "id": owner_id } }
        }
    )

    response = nodes_endpoint.post(object=node_object)


@click.command()
@click.option('-r', '--api-root', default='http://localhost:8888/api/v1/', show_default=True)
@click.option('-a', '--alias-prefix')
@click.argument("protocol-id")
@click.argument("model-id")
@click.argument("owner-id")
@click.argument("device-eui", nargs=-1)
def register_device_in_managair(api_root, alias_prefix, protocol_id, model_id, owner_id, device_eui):
    """Register Clair TTN nodes in the managair.

    \b
    PROTOCOL_ID is the id of the (existing) node protocol in the managair.
    MODEL_ID is the id of the (existing) node model in the managair.
    OWNER_ID is the id of the (existing) owner organization in the managair.
    DEVICE_EUI is the TTN device EUI.

    You will be prompted to enter usename and password of an account which
    needs to be a member of the owner organization. The account needs to have
    the right to create a node.
    """

    key = _login(api_root)

    for dev_eui in device_eui:
        _create_node(api_root, key, dev_eui, alias_prefix, protocol_id, model_id, owner_id)
