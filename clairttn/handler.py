import paho.mqtt.client as mqtt
import logging
import traceback
import base64
import dateutil.parser as dtparser
import datetime as dt
import json
import jsonapi_requests as jarequests
import clairttn.types as types
import clairttn.clairchen as clairchen
import clairttn.ers as ers
import clairttn.oy1012 as oy1012


class Rx_message:
    """Core parts of the TTN message received from a sensor"""

    def __init__(self, raw_data, device_eui, rx_datetime, rx_port, mcs):
        self.raw_data = raw_data
        self.device_eui = device_eui
        self.rx_datetime = rx_datetime
        self.rx_port = rx_port
        self.mcs = mcs


class _Handler:
    def __init__(self, app_id, access_key, stack):
        logging.debug("Application ID: %s", app_id)

        self.stack = stack
        if stack == "ttn-v2":
            logging.info("Configuring TTN Stack V2")
            self._broker_host = "eu.thethings.network"
            self._sub_topics = app_id + "/devices/+/up"
        elif stack == "ttn-v3":
            logging.info("Configuring TTN Stack V3")
            self._broker_host = "eu1.cloud.thethings.network"
            self._sub_topics = "v3/" + app_id + "@ttn/devices/+/up"
        else:
            raise AssertionError("Code path should not be reachable.")

        self._broker_port = 1883
        self._mqtt_client = mqtt.Client(
            client_id="Clair-Berlin",
            clean_session=False,
            userdata=None,
            protocol=mqtt.MQTTv311,
            transport="tcp",
        )
        self._mqtt_client.username_pw_set(username=app_id, password=access_key)

        def on_connect(client, _userdata, _flags, rc):
            if rc == 0:
                logging.info("Connect success!")
                client.subscribe(self._sub_topics)
                logging.debug("Subscribed to topic %s", self._sub_topics)
            else:
                logging.error("Failed to connect, return code %d", rc)

        def on_message(_client, _userdata, message):
            """Receive, decode and forward a TTN uplink message.

            Args:
                _unused_client (paho mqqt_client): Callback mqqq_client instance. Unused
                _unused_userdata ([type]): Unused
                message (bytes): Received mqqt message as byte-array.
            """
            
            topic = message.topic
            # Decode UTF-8 bytes to Unicode,
            mqtt_payload = message.payload.decode("utf8")
            # Parse the string into a JSON object.
            ttn_rxmsg = json.loads(mqtt_payload)
            logging.debug("Uplink message received on topic %s", topic)
            logging.debug("Message payload: %s", ttn_rxmsg)

            if stack == "ttn-v2":
                if not ttn_rxmsg["payload_raw"]:
                    logging.warning("message without payload, skipping...")
                    return
                rx_message = self._on_message_v2(ttn_rxmsg)
            else:  # ttn-v3
                if not ttn_rxmsg["uplink_message"]["frm_payload"]:
                    logging.warning("message without payload, skipping...")
                    return
                rx_message = self._on_message_v3(ttn_rxmsg)
            # Decoding the message is specific to each node type.
            # This is handled by a node-specific subclass.
            try:
                self._handle_message(rx_message)
            except Exception as e2:
                logging.error("exception during message handling: %s", e2)
                logging.error(traceback.format_exc())

        # Attach callbacks to client.
        self._mqtt_client.on_message = on_message
        self._mqtt_client.on_connect = on_connect

    def connect(self):
        logging.debug("Connecting to the TTN MQTT broker at %s", self._broker_host)
        self._mqtt_client.connect_async(host=self._broker_host, port=self._broker_port)

        self._mqtt_client.loop_start()
        logging.debug("Message handling loop started.")

    def disconnect_and_close(self):
        self._mqtt_client.loop_stop()
        logging.debug("Message handling loop stopped.")
        self._mqtt_client.disconnect()
        logging.debug("Disconnected from %s", self._broker_address)

    def _on_message_v2(self, ttn_rxmsg):
        try:
            device_eui = bytes.fromhex(ttn_rxmsg["hardware_serial"])
            logging.info("device eui: %s", device_eui.hex())

            device_id = ttn_rxmsg["dev_id"]
            logging.info("device name: %s", device_id)

            raw_payload = ttn_rxmsg["payload_raw"]
            raw_data = base64.b64decode(raw_payload)
            logging.debug("raw data: %s", raw_data.hex("-").upper())

            metadata = ttn_rxmsg["metadata"]
            rx_datetime = dtparser.parse(metadata["time"])
            logging.debug("received at: %s", rx_datetime.isoformat())

            rx_port = ttn_rxmsg.get("port", 5)  # Default Elsys ERS uplink port is 5.
            lora_rate = metadata["data_rate"]

        except Exception as e1:
            logging.error(
                "Exception decoding the MQTT message: %s \n error %s", ttn_rxmsg, e1
            )
        try:
            mcs = types.LoRaWanMcs[lora_rate]
        except KeyError:
            logging.warning("message without data rate, assuming simulated uplink")
            mcs = types.LoRaWanMcs.SF9BW125
        logging.info("MCS: %s", mcs)
        return Rx_message(raw_data, device_eui, rx_datetime, rx_port, mcs)

    def _on_message_v3(self, ttn_rxmsg):
        try:
            device_ids = ttn_rxmsg["end_device_ids"]
            device_eui = bytes.fromhex(device_ids["dev_eui"])
            logging.info("device eui: %s", device_eui.hex())

            device_id = device_ids["device_id"]
            logging.info("device name: %s", device_id)

            uplink_message = ttn_rxmsg["uplink_message"]
            raw_payload = uplink_message["frm_payload"]
            raw_data = base64.b64decode(raw_payload)
            logging.debug("raw data: %s", raw_data.hex("-").upper())

            rx_datetime = dtparser.parse(uplink_message["received_at"])
            logging.debug("received at: %s", rx_datetime.isoformat())

            # Default Elsys ERS uplink port is 5.
            rx_port = uplink_message.get("f_port", 5)
            lora_rate = uplink_message["settings"]["data_rate_index"]
        except Exception as e1:
            logging.error(
                "Exception decoding the MQTT message: %s \n error %s", ttn_rxmsg, e1
            )
        try:
            mcs = types.DATA_RATE_INDEX[lora_rate]
        except KeyError:
            logging.warning("message without data rate, assuming simulated uplink")
            mcs = types.LoRaWanMcs.SF9BW125
        logging.info("MCS: %s", mcs)
        return Rx_message(raw_data, device_eui, rx_datetime, rx_port, mcs)

    def _handle_message(self, rx_message):
        raise NotImplementedError("needs to be implemented by subclass")


class _SampleForwardingHandler(_Handler):
    def __init__(self, app_id, access_key, api_root, stack):
        super().__init__(app_id, access_key, stack)

        api = jarequests.Api.config(
            {
                "API_ROOT": api_root,
                "TIMEOUT": 5,  # we observed extreme timeouts with Django in DEBUG mode
                "RETRIES": 3,
            }
        )
        self._sample_endpoint = api.endpoint("ingest")

    def _handle_message(self, rx_message):
        uuid_class = self._get_uuid_class()
        device_uuid = uuid_class(rx_message.device_eui)
        logging.debug("device_uuid: %s", device_uuid)

        samples = self._decode_payload(rx_message)
        for sample in samples:
            # the ingest enpdoint expects the rel. humidity to be an integer
            if sample.relative_humidity:
                sample.relative_humidity.value = round(sample.relative_humidity.value)
            self._post_sample(sample, device_uuid)

    def _get_uuid_class(self):
        raise NotImplementedError("needs to be implemented by subclass")

    def _decode_payload(self, rx_message):
        raise NotImplementedError("needs to be implemented by subclass")

    def _post_sample(self, sample, device_uuid):
        logging.debug("sample: {}".format(sample))

        sample_attributes = {
            "timestamp_s": sample.timestamp.value,
            "co2_ppm": sample.co2.value,
        }
        if sample.temperature:
            sample_attributes["temperature_celsius"] = sample.temperature.value
        if sample.relative_humidity:
            sample_attributes["rel_humidity_percent"] = sample.relative_humidity.value

        sample_object = jarequests.JsonApiObject(
            type="Sample",
            attributes=sample_attributes,
            relationships={"node": {"data": {"type": "Node", "id": str(device_uuid)}}},
        )
        response = self._sample_endpoint.post(object=sample_object)
        logging.debug("response: {}".format(response))


class ClairchenForwardingHandler(_SampleForwardingHandler):
    """A handler for Clairchen devices which forwards samples to the backend API"""

    def _get_uuid_class(self):
        return clairchen.ClairchenDeviceUUID

    def _decode_payload(self, rx_message):
        return clairchen.decode_payload(
            rx_message.raw_data, rx_message.rx_datetime, rx_message.mcs
        )


class ErsForwardingHandler(_SampleForwardingHandler):
    """A handler for Elsys ERS devices which forwards samples to the backend API"""

    def _get_uuid_class(self):
        return ers.ErsDeviceUUID

    def _decode_payload(self, rx_message):
        return ers.decode_payload(rx_message.raw_data, rx_message.rx_datetime)


class Oy1012ForwardingHandler(_SampleForwardingHandler):
    """A handler for Talkpool OY1012 devices which forwards samples to the backend API"""

    def _get_uuid_class(self):
        return oy1012.Oy1012DeviceUUID

    def _decode_payload(self, rx_message):
        return oy1012.decode_payload(rx_message.raw_data, rx_message.rx_datetime)


class ErsConfigurationHandler(_Handler):
    """A handler for Elsys ERS devices which sends parameter downlink messages"""

    def _is_conforming(self, raw_data, mcs):
        measurement_count = len(ers.decode_payload(raw_data, dt.datetime.now()))
        logging.debug("measurement count: %d", measurement_count)
        logging.debug("mcs: {}".format(mcs))

        protocol_payload_specification = ers.PROTOCOL_PAYLOAD_SPECIFICATION[mcs]
        expected_measurement_count = protocol_payload_specification.measurement_count

        return measurement_count == expected_measurement_count

    def _handle_message(self, rx_message):
        if not self._is_conforming(raw_data=rx_message.raw_data, mcs=rx_message.mcs):
            logging.debug("message is not conforming to protocol payload specification")

            parameter_set = ers.PARAMETER_SETS[mcs]
            logging.debug("new parameter set: {}".format(parameter_set))

            payload = ers.encode_parameter_set(parameter_set)
            b64_payload = str(base64.b64encode(payload), "ascii")

            # ERS downlink payloads are sent on the configured port + 1
            tx_port = self.rx_port + 1

            logging.debug(
                "sending downlink payload %s (%s) to port %d",
                payload.hex(),
                b64_payload,
                tx_port,
            )

            self._mqtt_client.send(
                rx_message.device_eui, b64_payload, tx_port, conf=False
            )
