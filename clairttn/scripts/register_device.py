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
@click.option('-i', '--ttn-app-id', required=True)
@click.option('-k', '--access-key-file', required=True, type=click.File())
@click.argument("device-eui")
@click.argument("app-eui")
def register_device_in_ttn(ttn_app_id, access_key_file, device_eui, app_eui):
    """Register a Clair TTN node in the TTN.

    \b
    DEVICE_EUI is the TTN device EUI.
    APP_EUI is the TTN app EUI.
    """

    access_key = access_key_file.read().rstrip('\n')
    applicationClient = ttn.HandlerClient(ttn_app_id, access_key).application()

    device_id = str(ers.ErsDeviceUUID(bytes.fromhex(device_eui)))
    ttn_device = _create_ttn_device(device_eui, app_eui)

    applicationClient.register_device(device_id, ttn_device)


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


def _create_node(api_root, device_id, device_eui, protocol_id, model_id, owner_id):
    key = _login(api_root)

    api = jarequests.Api.config({
        'API_ROOT': api_root,
        'AUTH': _TokenAuth(key)
    })

    nodes_endpoint = api.endpoint('nodes')

    node_object = jarequests.JsonApiObject(
        type = 'Node',
        id = device_id,
        attributes = {
            "eui64": device_eui,
            "alias": device_eui
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
@click.argument("device-eui")
@click.argument("protocol-id")
@click.argument("model-id")
@click.argument("owner-id")
def register_device_in_managair(api_root, device_eui, protocol_id, model_id, owner_id):
    """Register a Clair TTN node in the managair.

    \b
    DEVICE_EUI is the TTN device EUI.
    PROTOCOL_ID is the id of the (existing) node protocol in the managair.
    MODEL_ID is the id of the (existing) node model in the managair.
    OWNER_ID is the id of the (existing) owner organization in the managair.

    You will be prompted to enter usename and password of an account which
    needs to be a member of the owner organization. The account needs to have
    the right to create a node.
    """
    device_id = str(ers.ErsDeviceUUID(bytes.fromhex(device_eui)))

    _create_node(api_root, device_id, device_eui, protocol_id, model_id, owner_id)
