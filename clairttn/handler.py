import ttn
import logging
import traceback
import base64
import dateutil.parser as dtparser
import datetime as dt
import jsonapi_requests as jarequests
import clairttn.types as types
import clairttn.clairchen as clairchen
import clairttn.ers as ers
import clairttn.oy1012 as oy1012


class _Handler:
    def __init__(self, app_id, access_key):
        logging.debug("app id: {}".format(app_id))

        ttnHandler = ttn.HandlerClient(app_id, access_key)
        self._mqtt_client = ttnHandler.data()

        def _uplink_callback(message, client):
            logging.debug("uplink message received from {}".format(message.dev_id))
            logging.debug(str(message))

            if not message.payload_raw:
                logging.warning("message without payload, skipping...")
                return

            try:
                payload = base64.b64decode(message.payload_raw)
                logging.debug("payload: {}".format(payload.hex('-').upper()))

                device_id = bytes.fromhex(message.hardware_serial)
                logging.debug("device_id: {}".format(device_id.hex()))

                self._handle_message(payload, device_id, message)

            except Exception as e:
                logging.error("exception during message handling: {}".format(e))
                logging.error(traceback.format_exc())

        self._mqtt_client.set_uplink_callback(_uplink_callback)

    def connect(self):
        self._mqtt_client.connect()

    def close(self):
        self._mqtt_client.close()

    def _handle_message(self, payload, device_id, message):
        raise NotImplementedError("needs to be implemented by subclass")


class _SampleForwardingHandler(_Handler):
    def __init__(self, app_id, access_key, api_root):
        super().__init__(app_id, access_key)

        api = jarequests.Api.config({ 'API_ROOT': api_root })
        self._sample_endpoint = api.endpoint('ingest')

    def _handle_message(self, payload, device_id, message):
        rx_datetime = dtparser.parse(message.metadata.time)
        logging.debug("rx_datetime: {}".format(rx_datetime))

        uuid_class = self._get_uuid_class()
        device_uuid = uuid_class(device_id)
        logging.debug("device_uuid: {}".format(device_uuid))

        samples = self._decode_payload(payload, rx_datetime, message)
        for sample in samples:
            self._post_sample(sample, device_uuid)

    def _get_uuid_class(self):
        raise NotImplementedError("needs to be implemented by subclass")

    def _decode_payload(self, payload, rx_datetime, message):
        raise NotImplementedError("needs to be implemented by subclass")

    def _post_sample(self, sample, device_uuid):
        logging.debug("sample: {}".format(sample))

        sample_attributes = {
            "timestamp_s": sample.timestamp.value,
            "co2_ppm": sample.co2.value
        }
        if sample.temperature:
            sample_attributes["temperature_celsius"] = sample.temperature.value
        if sample.relative_humidity:
            sample_attributes["rel_humidity_percent"] = sample.relative_humidity.value

        sample_object = jarequests.JsonApiObject(
            type = 'Sample',
            attributes = sample_attributes,
            relationships = {
                "node_ref_id": {
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
    """A handler for Clairchen devices which forwards samples to the backend API"""

    def __init__(self, app_id: str, access_key: str, api_root: str):
        super().__init__(app_id, access_key, api_root)

    def _get_uuid_class(self):
        return clairchen.ClairchenDeviceUUID

    def _decode_payload(self, payload, rx_datetime, message):
        try:
            mcs = types.LoRaWanMcs[message.metadata.data_rate]
        except:
            logging.warning("message without data rate, assuming simulated uplink")
            mcs = types.LoRaWanMcs.SF9BW125
        return clairchen.decode_payload(payload, rx_datetime, mcs)


class ErsForwardingHandler(_SampleForwardingHandler):
    """A handler for Elsys ERS devices which forwards samples to the backend API"""

    def __init__(self, app_id: str, access_key: str, api_root: str):
        super().__init__(app_id, access_key, api_root)

    def _get_uuid_class(self):
        return ers.ErsDeviceUUID

    def _decode_payload(self, payload, rx_datetime, message):
        return ers.decode_payload(payload, rx_datetime)


class Oy1012ForwardingHandler(_SampleForwardingHandler):
    """A handler for Talkpool OY1012 devices which forwards samples to the backend API"""

    def __init__(self, app_id: str, access_key: str, api_root: str):
        super().__init__(app_id, access_key, api_root)

    def _get_uuid_class(self):
        return oy1012.Oy1012DeviceUUID

    def _decode_payload(self, payload, rx_datetime, message):
        return oy1012.decode_payload(payload, rx_datetime)


class ErsConfigurationHandler(_Handler):
    """A handler for Elsys ERS devices which sends parameter downlink messages"""

    def _handle_message(self, payload, device_id, message):
        logging.debug("uplink message received from {}".format(message.dev_id))
        logging.debug(str(message))

        if not self._is_conforming(payload, message):
            logging.debug("message is not conforming to protocol payload specification")

            mcs = types.LoRaWanMcs[message.metadata.data_rate]
            parameter_set = ers.PARAMETER_SETS[mcs]
            logging.debug("new parameter set: {}".format(parameter_set))

            payload = ers.encode_parameter_set(parameter_set)
            b64_payload = str(base64.b64encode(payload), 'ascii')

            # ERS downlink payloads are sent on the configured port + 1
            port = message.port + 1

            logging.debug("sending downlink payload {} ({}) to port {}".format(payload.hex(), b64_payload, port))

            self._mqtt_client.send(message.dev_id, b64_payload, port, conf=False)

    def _is_conforming(self, payload, message):
        measurement_count = len(ers.decode_payload(payload, dt.datetime.now()))
        logging.debug("measurement count: {}".format(measurement_count))

        if not (hasattr(message, 'metadata') and hasattr(message.metadata, 'data_rate')):
            logging.warning("message without data_rate, assuming simulated uplink message")
            return True

        mcs = types.LoRaWanMcs[message.metadata.data_rate]
        logging.debug("mcs: {}".format(mcs))

        protocol_payload_specification = ers.PROTOCOL_PAYLOAD_SPECIFICATION[mcs]
        expected_measurement_count = protocol_payload_specification.measurement_count

        return measurement_count == expected_measurement_count
