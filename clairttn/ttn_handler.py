import logging
import paho.mqtt.client as mqtt
import json
import traceback
import base64
import dateutil.parser as dtparser
import clairttn.types as types


class RxMessage:
    """Core parts of the TTN message received from a node"""

    def __init__(self, raw_data, device_id, device_eui, rx_datetime, rx_port, mcs):
        self.raw_data = raw_data
        self.device_id = device_id
        self.device_eui = device_eui
        self.rx_datetime = rx_datetime
        self.rx_port = rx_port
        self.mcs = mcs


class _TtnHandler:
    def _handle_message(self, ttn_rxmsg):
        raise NotImplementedError("Needs to be provided as callback.")

    def _on_connect(self, client, _userdata, _flags, rc):
        if rc == 0:
            logging.info("Connect success!")
            client.subscribe(self._sub_topics)
            logging.debug("Subscribed to topic %s", self._sub_topics)
        else:
            logging.error("Failed to connect, return code %d", rc)

    def _on_message(self, _client, _userdata, message):
        # Decode UTF-8 bytes to Unicode,
        mqtt_payload = message.payload.decode("utf8")
        # Parse the string into a JSON object.
        ttn_rxmsg = json.loads(mqtt_payload)
        topic = message.topic
        logging.debug("Uplink message received on topic %s", topic)
        logging.debug("Message payload: %s", ttn_rxmsg)

        rx_message = self._extract_rx_message(ttn_rxmsg)
        if not rx_message:
            logging.warning("Skipping message...")
            return
        try:
            self.handle_message(rx_message)
        except Exception as e2:
            logging.error("exception during message handling: %s", e2)
            logging.error(traceback.format_exc())

    def __init__(self, app_id, access_key, broker_host, sub_topics):
        logging.debug("Application ID: %s", app_id)

        self._app_id = app_id
        self._broker_port = 1883  # TTN uses the default MQTT port.
        self._broker_host = broker_host
        self._sub_topics = sub_topics
        self._mqtt_client = mqtt.Client(
            client_id="Clair-Berlin",
            clean_session=False,
            userdata=None,
            protocol=mqtt.MQTTv311,  # TTN supports MQTT v 3.1.1 only
            transport="tcp",
        )
        self._mqtt_client.username_pw_set(username=app_id, password=access_key)

        # Attach callbacks to client.
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.on_connect = self._on_connect
        # Fake callback. Must be provided by appplication-layer node handler
        self.handle_message = self._handle_message

    def _extract_rx_message(self, ttn_rxmsg):
        raise NotImplementedError("needs to be implemented by subclass")

    def _create_tx_message(self, port, payload):
        raise NotImplementedError("needs to be implemented by subclass")

    def connect(self):
        if self._broker_host:
            logging.debug("Connecting to the TTN MQTT broker at %s", self._broker_host)
            self._mqtt_client.connect_async(
                host=self._broker_host, port=self._broker_port
            )

            self._mqtt_client.loop_start()
            logging.debug("Message handling loop started.")
        else:
            raise NotImplementedError("must be called from concrete subclass")

    def disconnect_and_close(self):
        self._mqtt_client.loop_stop()
        logging.debug("Message handling loop stopped.")
        self._mqtt_client.disconnect()
        logging.debug("Disconnected from %s", self._broker_host)

    def send(self, dev_id, port, payload):
        raise NotImplementedError("Must be implemented by subclass")


class TtnV2Handler(_TtnHandler):
    def __init__(self, app_id, access_key):
        logging.info("Configuring TTN Stack V2")
        sub_topics = app_id + "/devices/+/up"
        super().__init__(app_id, access_key, "eu.thethings.network", sub_topics)

    def _extract_rx_message(self, ttn_rxmsg):
        if "payload_raw" not in ttn_rxmsg:
            logging.warning("Message without payload.")
            return None
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
            return None
        try:
            mcs = types.LoRaWanMcs[lora_rate]
        except KeyError:
            logging.warning("message without data rate, assuming simulated uplink")
            mcs = types.LoRaWanMcs.SF9BW125
        logging.info("MCS: %s", mcs)
        return RxMessage(raw_data, device_id, device_eui, rx_datetime, rx_port, mcs)

    def _create_tx_message(self, port, payload):
        """Message format: https://www.thethingsnetwork.org/docs/applications/mqtt/api/#downlink-messages"""
        tx_message = {"port": port, "payload_raw": payload}
        json_tx_message = json.dumps(tx_message)
        return str(json_tx_message)

    def send(self, dev_id, port, payload):
        topic = self._app_id + "/devices/" + dev_id + "/down"
        message = self._create_tx_message(port, payload)
        self._mqtt_client.publish(topic, message)


class TtnV3Handler(_TtnHandler):
    def __init__(self, app_id, access_key):
        logging.info("Configuring TTN Stack V3")
        sub_topics = "v3/" + app_id + "@ttn/devices/+/up"
        super().__init__(app_id, access_key, "eu1.cloud.thethings.network", sub_topics)

    def _extract_rx_message(self, ttn_rxmsg):
        if "frm_payload" not in ttn_rxmsg["uplink_message"]:
            logging.warning("Message without payload.")
            return None
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
            lora_rate = uplink_message["settings"].get("data_rate_index")
            if lora_rate is None:
                logging.warning("message without data rate, assuming simulated uplink")
                mcs = types.LoRaWanMcs.SF9BW125
            else:
                mcs = types.DATA_RATE_INDEX[lora_rate]    
        except Exception as e1:
            logging.error(
                "Exception decoding the MQTT message: %s \n error %s", ttn_rxmsg, e1
            )
            return None
        logging.info("MCS: %s", mcs)
        return RxMessage(raw_data, device_id, device_eui, rx_datetime, rx_port, mcs)

    def _create_tx_message(self, port, payload):
        """Message format: https://www.thethingsindustries.com/docs/reference/data-formats/#downlink-messages"""
        tx_frame = {"f_port": port, "frm_payload": payload, "priority": "NORMAL"}
        tx_message = {"downlinks": [tx_frame]}
        json_tx_message = json.dumps(tx_message)
        return str(json_tx_message)

    def send(self, dev_id, port, payload):
        topic = "v3/" + self._app_id + "@ttn/devices/" + dev_id + "/down/push"
        message = self._create_tx_message(port, payload)
        self._mqtt_client.publish(topic, message)
