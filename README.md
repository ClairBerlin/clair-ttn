# clairttners

Application for The Things Network (TTN) which subscribes to the ESR uplink
messages and sends downlink configuration messages, if the transmission scheme
does not match the current datarate.

## Development Setup

```
git submodule init
git submodule update
. development.env
python3 -m venv env
. env/bin/activate
pip install -r inspectair/requirements.txt
pip install --editable .
```

Afterwards, the `clairttners` command should be available
([source](https://click.palletsprojects.com/en/7.x/setuptools/#testing-the-script)).

## Usage

```
Usage: clairttners [OPTIONS]

Options:
  -i, --app-id TEXT               [default: clair-berlin-ers-co2]
  -k, --access-key-file FILENAME  [required]
  --help                          Show this message and exit.
```

The app id and the access key file parameters can also be specified as the
environment variables `TTN_APP_ID` and `TTN_ACCESS_KEY_FILE`.
