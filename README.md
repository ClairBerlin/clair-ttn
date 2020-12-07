# Clair Things Network Application

Clair-TTN is part of the _Clair Platform_, a system to collect measurements from networked CO2-sensors for indoor air-quality monitoring. It is developed and run by the [Clair Berlin Initiative](https://clair-berlin.de), a non-profit, open-source initiative to help operators of public spaces lower the risk of SARS-CoV2-transmission amongst their patrons.

Technically speaking, Clair-TTN is a service in the [Clair Stack](https://github.com/ClairBerlin/clair-stack), which is the infrastructure-as-code implementation of the Clair Platform.

The application for The Things Network (TTN) can be run in the following modes:

* Clairchen forwarding: subscribes to uplink messages of Clairchen nodes,
  decodes them and forwards measurement samples to the ingest endpoint of the
  backend API.
* ERS forwarding: does the sampe for ERS nodes.
* ERS configuration: subscribes to uplink messages of ERS nodes and sends
  downlink messages to update the sensor's parameters to meet the TTN's airtime
  constraints.
* OY1012 forwarding: forwarding for Talkpool OY1012.

## Development Setup

```
python3 -m venv env
. env/bin/activate
pip install --editable .
```

Afterwards, the `clairttn` command should be available
([source](https://click.palletsprojects.com/en/7.x/setuptools/#testing-the-script)).

## Usage

```
Usage: clairttn [OPTIONS]

Options:
  -i, --app-id TEXT               [default: clair-berlin-ers-co2]
  -k, --access-key-file FILENAME  [required]
  -m, --mode [clairchen-forward|ers-forward|ers-configure|oy1012-forward]
                                  [required]
  -r, --api-root TEXT             [default: http://localhost:8888/ingest/v1/]
  --help                          Show this message and exit.
```

The app id, the access key file, the mode, and the api root parameter can also
be specified as the following environment variables:

* app id: `CLAIR_TTN_APP_ID`
* access key: `CLAIR_TTN_ACCESS_KEY_FILE`
* mode: `CLAIR_MODE`
* api root: `CLAIR_API_ROOT`

# Management Tools

## clair-register-device-in-ttn

```
Usage: clair-register-device-in-ttn [OPTIONS] APP_ID ACCESS_KEY_FILE APP_EUI
                                    [DEVICE_EUI]...

  Register Clair TTN nodes in the TTN.

  APP_ID is the TTN application id.
  ACCESS_KEY_FILE is the file that contains the access key of the TTN application.
  APP_EUI is the TTN app EUI.
  DEVICE_EUI is the TTN device EUI.

Options:
  --help  Show this message and exit.
```

## clair-register-device-in-managair

```
Usage: clair-register-device-in-managair [OPTIONS] PROTOCOL_ID MODEL_ID
                                         OWNER_ID [DEVICE_EUI]...

  Register Clair TTN nodes in the managair.

  PROTOCOL_ID is the id of the (existing) node protocol in the managair.
  MODEL_ID is the id of the (existing) node model in the managair.
  OWNER_ID is the id of the (existing) owner organization in the managair.
  DEVICE_EUI is the TTN device EUI.

  You will be prompted to enter usename and password of an account which
  needs to be a member of the owner organization. The account needs to have
  the right to create a node.

Options:
  -r, --api-root TEXT      [default: http://localhost:8888/api/v1/]
  -a, --alias-prefix TEXT
  --help                   Show this message and exit.
```

## clair-generate-nfc-config

```
Usage: clair-generate-nfc-config [OPTIONS] DEVICE_EUI

  Create NFC config files for a device registered in the TTN.

  DEVICE_EUI is the TTN device EUI.

Options:
  -i, --ttn-app-id TEXT           [required]
  -k, --access-key-file FILENAME  [required]
  --help                          Show this message and exit.
```

## clair-generate-fixtures-from-backup

```
Usage: clair-generate-fixtures-from-backup [OPTIONS] BASE_URL ACCESS_KEY_FILE

  Generate fixtures from the TTN's DB integration.

  BASE_URL is the base URL of the TTN's DB integration API.
  ACCESS_KEY_FILE is the file containing the TTN app's access key.

Options:
  -p, --payload-type TEXT  [default: ers]
  -d, --duration TEXT      [default: 1d]
  --help                   Show this message and exit.
```
