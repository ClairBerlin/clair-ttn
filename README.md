# clairttn

Application for The Things Network (TTN) which can be run in one of three modes:

* Clairchen forwarding: subscribes to uplink messages of Clairchen nodes,
  decodes them and forwards measurement samples to the ingest endpoint of the
  backend API.
* ERS forwarding: does the sampe for ERS nodes.
* ERS configuration: subscribes to uplink messages of ERS nodes and sends
  downlink messages to update the sensor's parameters to meet the TTN's airtime
  constraints.

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
  -m, --mode [clairchen-forward|ers-forward|ers-configure]
                                  [required]
  -r, --api-root TEXT             [default:
                                  http://localhost:8888/api/data/v1/]

  --help                          Show this message and exit.
```

The app id, the access key file, the mode, and the api root parameter can also
be specified as the following environment variables:

* app id: `CLAIR_TTN_APP_ID`
* access key: `CLAIR_TTN_ACCESS_KEY_FILE`
* mode: `CLAIR_MODE`
* api root: `CLAIR_API_ROOT`
