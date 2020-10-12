import ttn
import logging
import base64
import dateutil.parser as dtparser
import datetime as dt
import clairttn.ers as ers


class _Handler:
    def __init__(self, app_id, access_key):
        logging.debug("app id: {}".format(app_id))
        logging.debug(type(self))
        ttnHandler = ttn.HandlerClient(app_id, access_key)
        self._mqtt_client = ttnHandler.data()

        def _uplink_callback(message, client):
            logging.debug("uplink message received from {}".format(message.dev_id))
            logging.debug(str(message))

            payload = base64.b64decode(message.payload_raw)
            logging.debug("decoded payload: {}".format(payload.hex('-').upper()))

            self._handle_message(payload, message)

        self._mqtt_client.set_uplink_callback(_uplink_callback)

    def connect(self):
        self._mqtt_client.connect()

    def close(self):
        self._mqtt_client.close()

    def _handle_message(self, payload, message):
        raise NotImplementedError("needs to be implemented by subclass")


class _SampleForwardingHandler(_Handler):
    def _handle_message(self, payload, message):
        rx_datetime = dtparser.parse(message.metadata.time)
        logging.debug("rx_datetime: {}".format(rx_datetime))
        samples = self._decode_payload(payload, rx_datetime)
        for sample in samples:
            logging.debug(sample)
            logging.debug(dt.datetime.fromtimestamp(sample.timestamp))
            logging.debug(sample.co2)
            logging.debug(sample.temperature)
            logging.debug(sample.relative_humidity)

    def _decode_payload(self, payload, rx_datetime):
        raise NotImplementedError("needs to be implemented by subclass")


class ClairchenForwardingHandler(_SampleForwardingHandler):
    pass


class ErsForwardingHandler(_SampleForwardingHandler):
    def _decode_payload(self, payload, rx_datetime):
        return ers.decode_payload(payload, rx_datetime)


class ErsConfigurationHandler(_Handler):
    def _handle_message(self, payload, message):
        logging.debug("uplink message received from {}".format(message.dev_id))
        logging.debug(str(message))

        if not self._is_conforming(payload):
            logging.debug("message is not conforming to protocol payload specification")

            mcs = LoRaWanMcs[message.metadata.data_rate]
            parameter_set = ERS_PARAMETER_SETS[mcs]
            logging.debug("new parameter set: {}".format(parameter_set))

            payload = _encode_parameter_set(parameter_set)
            b64_payload = str(base64.b64encode(payload), 'ascii')

            # ERS downlink payloads are sent on the configured port + 1
            port = message.port + 1

            logging.debug("sending downlink payload {} ({}) to port {}".format(payload.hex(), b64_payload, port))

            self._mqtt_client.send(message.dev_id, b64_payload, port, conf=False)

    def _is_conforming(self, payload):
        measurement_count = len(ers.decode_payload(payload))
        logging.debug("measurement count: {}".format(measurement_count))

        if not (hasattr(message, 'metadata') and hasattr(message.metadata, 'data_rate')):
            logging.warning("message without data_rate, assuming simulated uplink message")
            return True

        mcs = LoRaWanMcs[message.metadata.data_rate]
        logging.debug("mcs: {}".format(mcs))

        protocol_payload_specification = ers.PROTOCOL_PAYLOAD_SPECIFICATION[mcs]
        expected_measurement_count = protocol_payload_specification.measurement_count

        return measurement_count == expected_measurement_count