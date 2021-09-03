import logging
import paho.mqtt.client as mqtt
import json
import traceback
import base64
import dateutil.parser as dtparser
import clairttn.types as types


class RxMessage:
    """Core parts of the TTN message received from a node"""

    def __init__(self, raw_data, device_eui, rx_datetime, rx_port, mcs):
        self.raw_data = raw_data
        self.device_eui = device_eui
        self.rx_datetime = rx_datetime
        self.rx_port = rx_port
        self.mcs = mcs


class TxMessage:
    """Message payload and information to transmit on a downlink."""

    def __init__(self, device_eui, tx_port, b64_payload):
        self.device_eui = device_eui
        self.tx_port = tx_port
        self.b64_payload = b64_payload


class _TtnHandler:
    def __init__(self, app_id, access_key, node_handler, broker_host, sub_topics):
        logging.debug("Application ID: %s", app_id)

        self.node_handler = node_handler
        self._broker_port = 1883
        self._broker_host = broker_host
        self._sub_topics = sub_topics
        self._mqtt_client = mqtt.Client(
            client_id="Clair-Berlin",
            clean_session=False,
            userdata=None,
            protocol=mqtt.MQTTv311,
            transport="tcp",
        )
        self._mqtt_client.username_pw_set(username=app_id, password=access_key)

        def _on_connect(client, _userdata, _flags, rc):
            if rc == 0:
                logging.info("Connect success!")
                client.subscribe(self._sub_topics)
                logging.debug("Subscribed to topic %s", self._sub_topics)
            else:
                logging.error("Failed to connect, return code %d", rc)

        def _on_message(_client, _userdata, message):
            # Decode UTF-8 bytes to Unicode,
            mqtt_payload = message.payload.decode("utf8")
            # Parse the string into a JSON object.
            ttn_rxmsg = json.loads(mqtt_payload)
            topic = message.topic
            logging.debug("Uplink message received on topic %s", topic)
            logging.debug("Message payload: %s", ttn_rxmsg)

            rx_message = self._extract_ttn_message(ttn_rxmsg)
            if not rx_message:
                logging.warning("Message without payload, skipping...")
                return
            try:
                # The message handler may choose to send a downlink message to the node
                # in return. Otherwise, response = None
                response = self.node_handler.handle_message(rx_message)
                if response:
                    logging.debug(
                        "sending downlink payload %s (%s) to port %d",
                        response.payload.hex(),
                        response.b64_payload,
                        response.tx_port,
                    )
                    self._mqtt_client.send(
                        response.device_eui,
                        response.b64_payload,
                        response.tx_port,
                        conf=False,
                    )
            except Exception as e2:
                logging.error("exception during message handling: %s", e2)
                logging.error(traceback.format_exc())

        # Attach callbacks to client.
        self._mqtt_client.on_message = _on_message
        self._mqtt_client.on_connect = _on_connect

    def _extract_ttn_message(self, ttn_rxmsg):
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


class TtnV2Handler(_TtnHandler):
    def __init__(self, app_id, access_key, node_handler):
        logging.info("Configuring TTN Stack V2")
        sub_topics = app_id + "/devices/+/up"
        super().__init__(
            app_id, access_key, node_handler, "eu.thethings.network", sub_topics
        )

    def _extract_ttn_message(self, ttn_rxmsg):
        if not ttn_rxmsg["payload_raw"]:
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
        try:
            mcs = types.LoRaWanMcs[lora_rate]
        except KeyError:
            logging.warning("message without data rate, assuming simulated uplink")
            mcs = types.LoRaWanMcs.SF9BW125
        logging.info("MCS: %s", mcs)
        return RxMessage(raw_data, device_eui, rx_datetime, rx_port, mcs)


class TtnV3Handler(_TtnHandler):
    def __init__(self, app_id, access_key, node_handler):
        logging.info("Configuring TTN Stack V3")
        sub_topics = "v3/" + app_id + "@ttn/devices/+/up"
        super().__init__(
            app_id, access_key, node_handler, "eu1.cloud.thethings.network", sub_topics
        )

    def _extract_ttn_message(self, ttn_rxmsg):
        if not ttn_rxmsg["uplink_message"]["payload_raw"]:
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
        return RxMessage(raw_data, device_eui, rx_datetime, rx_port, mcs)
