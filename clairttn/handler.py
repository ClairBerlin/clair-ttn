import ttn
import logging
import base64
import dateutil.parser as dtparser
import datetime as dt
import jsonapi_requests as jarequests
import clairttn.ers as ers
import clairttn.clairchen as clairchen


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

            device_id = bytes.fromhex(message.hardware_serial)
            logging.debug("device_id: {}".format(device_id.hex()))

            self._handle_message(payload, device_id, message)

        self._mqtt_client.set_uplink_callback(_uplink_callback)

    def connect(self):
        self._mqtt_client.connect()

    def close(self):
        self._mqtt_client.close()

    def _handle_message(self, payload, device_id, message):
        raise NotImplementedError("needs to be implemented by subclass")


class _SampleForwardingHandler(_Handler):
    def __init__(self, app_id, access_key):
        super().__init__(app_id, access_key)
        api = jarequests.Api.config({
            'API_ROOT': 'http://localhost:8888/api/data/v1/'
        })
        self._sample_endpoint = api.endpoint('ingest')

    def _handle_message(self, payload, device_id, message):
        rx_datetime = dtparser.parse(message.metadata.time)
        logging.debug("rx_datetime: {}".format(rx_datetime))

        device_uuid = self._uuid_class(device_id)
        logging.debug("device_uuid: {}".format(device_uuid))

        samples = self._decode_payload(payload, rx_datetime, message)
        for sample in samples:
            self._post_sample(sample, device_uuid)

    def _decode_payload(self, payload, rx_datetime, message):
        raise NotImplementedError("needs to be implemented by subclass")

    def _post_sample(self, sample, device_uuid):
        logging.debug("timestamp: {}".format(dt.datetime.fromtimestamp(sample.timestamp)))
        logging.debug("co2: {}".format(sample.co2))
        logging.debug("temperature: {}".format(sample.temperature))
        logging.debug("humidity: {}".format(sample.relative_humidity))

        sample_attributes = {
            "timestamp_s": sample.timestamp,
            "co2_ppm": sample.co2.value
        }
        if sample.temperature:
            sample_attributes["temperature_celsius"] = sample.temperature.value
        if sample.relative_humidity:
            sample_attributes["rel_humidity_percent"] = sampe.relative_humidity.value

        sample_object = jarequests.JsonApiObject(
            type = 'Sample',
            attributes = sample_attributes,
            relationships = {
                "node_ref": {
                    "data": {
                        "type": "Node",
                        "id": str(device_uuid)
                    }
                }
            }
        )

        response = self._sample_endpoint.post(object=sample_object)
        logging.debug("response: {}".format(response))


class ClairchenForwardingHandler(_SampleForwardingHandler):
    def __init__(self, app_id, access_key):
        super().__init__(app_id, access_key)
        self._uuid_class = clairchen.ClairchenDeviceUUID

    def _decode_payload(self, payload, rx_datetime, message):
        mcs = LoRaWanMcs[message.metadata.data_rate]
        return clairchen.decode_payload(payload, rx_datetime, mcs)


class ErsForwardingHandler(_SampleForwardingHandler):
    def __init__(self, app_id, access_key):
        super().__init__(app_id, access_key)
        self._uuid_class = ers.ErsDeviceUUID

    def _decode_payload(self, payload, rx_datetime, message):
        return ers.decode_payload(payload, rx_datetime)


class ErsConfigurationHandler(_Handler):
    def _handle_message(self, payload, device_id, message):
        logging.debug("uplink message received from {}".format(message.dev_id))
        logging.debug(str(message))

        if not self._is_conforming(payload, message):
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

    def _is_conforming(self, payload, message):
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
