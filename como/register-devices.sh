#!/usr/bin/env bash

set -e # fail on error

fail_usage() {
	echo $1
	echo "usage: register-device.sh JOIN_EUI DEV_EUI..."
	exit 1
}

protocol_id="2" # ELSYSERSPROT_V01
model_id="2" # ELSYS_ERS_CO2
org_id="17" # Technologiestiftung Berlin

app_id="elsys-ers-co2" # TTN app id

register_device() {
	dev_eui="$1"
	
	test -n "$dev_eui" || fail_usage "DEV_EUI not specified"
	
	# register in managair
	clair-register-in-managair -r https://clair-berlin.de/api/v1/ $protocol_id $model_id $org_id $dev_eui
	
	dev_id=`clair-get-device-id $dev_eui`
	
	# register in TTN
	ttn-lw-cli end-devices create $app_id $dev_id --dev-eui $dev_eui --join-eui $join_eui --frequency-plan-id EU_863_870 --with-root-keys --lorawan-version 1.0.3 --lorawan-phy-version 1.0.3-a
	
	# get app_key 
	app_key=`ttn-lw-cli end-devices get $app_id $dev_id --root-keys | python3 -c "import sys, json; print(json.load(sys.stdin)['root_keys']['app_key']['key'])"`
	
	clair-generate-nfc-config $join_eui $dev_eui $app_key
}

join_eui="$1"
test -n "$join_eui" || fail_usage "JOIN_EUI not specified"
shift

for dev_eui in "$@"; do
	register_device $dev_eui
done
