#!/usr/bin/env python3

import click
import requests
import base64
import json
import clairttn.ers as ers
import clairttn.clairchen as clairchen
import clairttn.types as types
import dateutil.parser as dtparser


UUID_MAP = {
    'clairfeatherprotored': 'c727b2f8-8377-d4cb-0e95-ac03200b8c93', # Clairchen Rot
    'clairprotoblack': '3b95a1b2-74e7-9e98-52c4-4acae441f0ae', # Clairchen Schwarz
    'ers-co2-sample1': str(ers.ErsDeviceUUID(bytes.fromhex('a81758fffe052b0f'))),
    'ers-co2-lite-hpi-a81758fffe052b0f': '9d02faee-4260-1377-22ec-936428b572ee',
    'ers-co2-lite-hpi-a81758fffe053c13': '6fbb3d55-c86b-e021-3ec3-b45425d5b1ba',
    'ers-co2-lite-hpi-a81758fffe053c14': '0cc5e5eb-93ad-a18f-bbfe-ef7f36c62ff8',
    'ers-co2-lite-hpi-a81758fffe053cab': 'f40f528b-9d0e-c2be-38fc-962f8757e531',
    'ers-co2-lite-hpi-a81758fffe053cac': '9f9f30bd-d8a6-0269-cf9e-f377d02986c4',
    'ers-co2-lite-hpi-a81758fffe053cad': '7f255730-b7bc-cc51-248f-71152d2edd79',
    'ers-co2-lite-hpi-a81758fffe053cae': 'cd8e32d5-a17f-915e-9cb7-5d401a550312'
}


@click.command()
@click.option('-b', '--base-url', default='https://eu1.cloud.thethings.network/', show_default=True)
@click.option('-d', '--duration', default='24h', show_default=True)
@click.argument('application-id')
@click.argument('access-key-file', type=click.File())
def generate_fixtures(application_id, access_key_file, base_url, duration):
    """Generate fixtures from the TTN's Storage integration (v3).

    \b
    APPLICATIION_ID is the id of the TTN app.
    ACCESS_KEY_FILE is the file containing the TTN app's access key.
    """

    access_key = access_key_file.read().rstrip('\n')

    headers = {
        'Accept': 'application/json',
        'Authorization': "Bearer {}".format(access_key)
    }

    base_url = base_url.rstrip('/ ')

    url = "{}/api/v3/as/applications/{}/packages/storage/uplink_message".format(base_url, application_id)

    params = { 'last': duration }

    response = requests.get(url, headers=headers, params=params)

    pdus = list(map(lambda l: json.loads(l), response.text.splitlines()))

    fixtures = []
    for pdu in pdus:
        payload = base64.b64decode(pdu['result']['uplink_message']['frm_payload'])
        rx_datetime = dtparser.parse(pdu['result']['uplink_message']['received_at'])
        device_id = pdu['result']['end_device_ids']['device_id']
        try:
            samples = ers.decode_payload(payload, rx_datetime)
        except types.PayloadContentException:
            continue
        for sample in samples:
            fields = {
                'node': UUID_MAP.get(device_id, device_id),
                'timestamp_s': sample.timestamp.value,
                'co2_ppm': sample.co2.value,
                'measurement_status': 'M'
            }
            if sample.temperature:
                fields['temperature_celsius'] = sample.temperature.value
            if sample.relative_humidity:
                fields['rel_humidity_percent'] = sample.relative_humidity.value

            fixture = {
                'model': 'core.sample',
                'fields': fields
            }

            fixtures.append(fixture)

    fixtures.sort(key=lambda f: f['fields']['timestamp_s'])
    print(json.dumps(fixtures, indent=4))
