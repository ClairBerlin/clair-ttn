#!/usr/bin/env python3

import click
import clairttn.ers as ers
import sys
import requests
import jsonapi_requests as jarequests
import json
import getpass


class _TokenAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = "Token {}".format(self.token)
        return r


def _login(api_root):
    login_endpoint = jarequests.Api.config({"API_ROOT": api_root}).endpoint(
        "auth/login"
    )

    username = input("Username: ")
    password = getpass.getpass()

    login_object = jarequests.JsonApiObject(
        type="LoginView", attributes={"username": username, "password": password}
    )

    try:
        r = login_endpoint.post(object=login_object)
    except jarequests.request_factory.ApiClientError as e:
        error_object = json.loads(e.content)
        print("login failed: {}".format(error_object["errors"][0]["detail"]))
        sys.exit(1)

    return r.data.attributes["key"]


def _create_node(
    api_root, key, device_eui, alias_prefix, protocol_id, model_id, owner_id
):
    api = jarequests.Api.config({"API_ROOT": api_root, "AUTH": _TokenAuth(key)})

    nodes_endpoint = api.endpoint("nodes")

    device_id = str(ers.ErsDeviceUUID(bytes.fromhex(device_eui)))

    node_object = jarequests.JsonApiObject(
        type="Node",
        id=device_id,
        attributes={
            "eui64": device_eui,
            "alias": "{}{}".format(alias_prefix, device_eui),
        },
        relationships={
            "protocol": {"data": {"type": "Protocol", "id": protocol_id}},
            "model": {"data": {"type": "Model", "id": model_id}},
            "owner": {"data": {"type": "Organization", "id": owner_id}},
        },
    )

    return nodes_endpoint.post(object=node_object)


@click.command()
@click.option(
    "-r", "--api-root", default="http://localhost:8888/api/v1/", show_default=True
)
@click.option("-a", "--alias-prefix")
@click.argument("protocol-id")
@click.argument("model-id")
@click.argument("owner-id")
@click.argument("device-eui", nargs=-1)
def register_device_in_managair(
    api_root, alias_prefix, protocol_id, model_id, owner_id, device_eui
):
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
        response = _create_node(
            api_root, key, dev_eui, alias_prefix, protocol_id, model_id, owner_id
        )
        print(response)
