#!/usr/bin/env python3

import click
import requests
import base64
import json
import clairttn.ers as ers
import clairttn.clairchen as clairchen
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
@click.option('-b', '--base_url', required=True)
@click.option('-k', '--access-key-file', envvar='CLAIR_TTN_ACCESS_KEY_FILE', required=True, type=click.File())
@click.option('-p', '--payload-type', default='ers', show_default=True)
@click.option('-d', '--duration', default='1d', show_default=True)
def get_fixtures(base_url, access_key_file, payload_type, duration):

    access_key = access_key_file.read().rstrip('\n')

    headers = {
        'Accept': 'application/json',
        'Authorization': "key {}".format(access_key)
    }

    url = "{}/api/v2/query".format(base_url)

    params = { 'last': duration }

    pdus = requests.get(url, headers=headers, params=params).json()

    fixtures = []
    for pdu in pdus:
        payload = base64.b64decode(pdu['raw'])
        rx_datetime = dtparser.parse(pdu['time'])
        samples = ers.decode_payload(payload, rx_datetime)
        for sample in samples:
            fields = {
                'node': UUID_MAP.get(pdu['device_id'], pdu['device_id']),
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

if __name__ == '__main__':
    get_fixtures()
