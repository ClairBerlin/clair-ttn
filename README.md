# Clair Things Network Application

Clair-TTN is part of the _Clair Platform_, a system to collect measurements from networked CO2-sensors for indoor air-quality monitoring. It is developed and run by the [Clair Berlin Initiative](https://clair-berlin.de), a non-profit, open-source initiative to help operators of public spaces lower the risk of SARS-CoV2-transmission amongst their patrons.

Technically speaking, Clair-TTN is a service in the [Clair Stack](https://github.com/ClairBerlin/clair-stack), which is the infrastructure-as-code implementation of the Clair Platform.

The application for The Things Network (TTN) supports both the legacy V2 stack as well as the new V3 stack.
It can be run in the following modes:

* Clairchen forwarding: subscribes to uplink messages of Clairchen nodes, decodes them and forwards measurement samples to the ingest endpoint of the backend API.
* ERS forwarding: does the sampe for ERS nodes.
* ERS configuration: subscribes to uplink messages of ERS nodes and sends downlink messages to update the sensor's parameters to meet the TTN's airtime constraints.
* OY1012 forwarding: forwarding for Talkpool OY1012.

In addition to the TTN application, this repository also contains a couple of TTN device management tools documented below.

## Development Setup

```shell
python3 -m venv env
. env/bin/activate
pip install wheel
pip install --editable .
```

Afterwards, the `clairttn` command should be available ([source](https://click.palletsprojects.com/en/7.x/setuptools/#testing-the-script)).

### Tests

`pytest` tests can be run like this:

```shell
python3 setup.py test
```

## Usage

```shell
Usage: clair-ttn [OPTIONS]

  Clair TTN application that can be run in one of the following modes:

  * Clairchen forwarding
  * ERS forwarding
  * ERS configuration
  * OY1012 forwarding

Options:
  -i, --app-id TEXT               [default: clair-berlin-ers-co2]
  -k, --access-key-file FILENAME  [required]
  -m, --mode [clairchen-forward|ers-forward|ers-configure|oy1012-forward]
                                  [required]
  -r, --api-root TEXT             [default: http://localhost:8888/ingest/v1/]
  -s, --stack [ttn-v2|ttn-v3]     [default: ttn-v2]
  --help                          Show this message and exit.
```

The following parameters can also be specified as environment variables:

* app id: `CLAIR_TTN_APP_ID`
* access key: `CLAIR_TTN_ACCESS_KEY_FILE`
* mode: `CLAIR_MODE`
* api root: `CLAIR_API_ROOT`
* stack: `CLAIR_TTN_STACK`

## TTN Node Management Tools

### Device Registration (TTN v3)

Registering a TTN node is a three-step process:

* Register managair node using `clair-register-device-in-managair`.
* TTN
  1. Register TTN device using `ttn-lw-cli`.
  2. Device configuration using `clair-generate-nfc-config` and the [NFC Tools app for iOS](https://www.wakdev.com/en/apps/nfc-tools-ios.html).

Note that, currently, only the [ERS CO2](https://www.elsys.se/en/ers-co2/) and [ERS CO2 Lite](https://www.elsys.se/en/ers-co2-lite/) sensors by [ELSYS](https://www.elsys.se/) are supported by these tools.

#### clair-register-device-in-managair

`clair-register-device-in-managair` computes the managair device id from the device's TTN EUI and creates a corresponding node owned by the organization identified by OWNER_ID.

```shell
Usage: clair-register-device-in-managair [OPTIONS] PROTOCOL_ID MODEL_ID
                                         OWNER_ID [DEVICE_EUI]...

  Register Clair TTN nodes in the managair.

  PROTOCOL_ID is the id of the (existing) node protocol in the managair.
  MODEL_ID is the id of the (existing) node model in the managair.
  OWNER_ID is the id of the (existing) owner organization in the managair.
  DEVICE_EUI is the TTN device EUI.

  You will be prompted to enter usename and password of an account which needs
  to be a member of the owner organization. The account needs to have the
  right to create a node.

Options:
  -r, --api-root TEXT      [default: http://localhost:8888/api/v1/]
  -a, --alias-prefix TEXT
  --help                   Show this message and exit.
```

#### clair-generate-nfc-config

`clair-generate-nfc-config` writes the TTN application EUI and the TTN application key to a text file and a PNG QR code which can be read using the [NFC Tools app for iOS](https://www.wakdev.com/en/apps/nfc-tools-ios.html). Both files are created in the working directory as `${DEV_EUI}-nfc-config.txt` and `${DEV_EUI}-nfc-config.png`, respectively. Existing files are overwritten!

```shell
Usage: clair-generate-nfc-config [OPTIONS] JOIN_EUI DEV_EUI APP_KEY

  Create NFC config files for Elsys ERS CO2 sensors..

  APP_EUI is the TTN application EUI.
  DEV_EUI is the TTN device EUI.
  APP_KEY is the TTN's app_key root key.

Options:
  --help  Show this message and exit.
```

#### clair-get-device-id

`clair-get-device-id` converts the device EUI of an Elsys ERS sensor node to the internal Clair device id.

```shell
Usage: clair-get-device-id [OPTIONS] DEV_EUI

  Convert a device EUI of an Elsys ERS sensor node to the corresponding
  managair device id.

  DEV_EUI is the LoraWAN device EUI.

Options:
  --help  Show this message and exit.
```

#### Registering devices with the TTN (v3) using `ttn-lw-cli`

[`ttn-lw-cli`](https://www.thethingsindustries.com/docs/getting-started/cli/) is the TTN's official command-line interface. Clair sensor nodes can be registered with a TTN application using the `end-devices create` command as follows:

```shell
ttn-lw-cli end-devices create $app_id $dev_id \
  --dev-eui $dev_eui \
  --join-eui $join_eui \
  --frequency-plan-id EU_863_870 \
  --with-root-keys \
  --lorawan-version 1.0.3 \
  --lorawan-phy-version 1.0.3-a
```

The following variables must be provided:

* `$app_id`: the id of your TTN application,
* `$dev_id`: the managair device id as returned by `clair-get-device-id`.
* `$join_eui`: the TTN device's JoinEUI, which may be specific to the device or the application.

We add the `--with-root-keys` option to have root keys generated. The application key needs to be passed on to `clair-generate-nfc-config`. To read back the key you can use the following command:

```shell
app_key=`ttn-lw-cli end-devices get $app_id $dev_id --root-keys | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['root_keys']['app_key']['key'])"`
```

[register-devices.sh](como/register-devices.sh) is an exemplary wrapper script written for the Berlin COMo project.

### Restoring data from the TTN's Storage Integration (TTN v3 only)

The [TTN Storage Integration](https://www.thethingsindustries.com/docs/integrations/storage/), if enabled, persists your TTN application's data for seven days. `clair-generate-fixtures-from-storage` reads this data and converts it to fixtures which can be read by Django's [`loaddata`](https://docs.djangoproject.com/en/3.1/ref/django-admin/#loaddata) command.

#### clair-generate-fixtures-from-storage

```shell
Usage: clair-generate-fixtures-from-storage [OPTIONS] APPLICATION_ID
                                            ACCESS_KEY_FILE

  Generate fixtures from the TTN's Storage integration (v3).

  APPLICATIION_ID is the id of the TTN app.
  ACCESS_KEY_FILE is the file containing the TTN app's access key.

Options:
  -b, --base-url TEXT  [default: https://eu1.cloud.thethings.network/]
  -d, --duration TEXT  [default: 24h]
  --help               Show this message and exit.
```
