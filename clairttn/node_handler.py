import logging
import base64
import datetime as dt
import jsonapi_requests as jarequests
import clairttn.clairchen as clairchen
import clairttn.ers as ers
import clairttn.oy1012 as oy1012


class _NodeHandler:
    def __init__(self, ttn_client):
        self.ttn_client = ttn_client
        self.ttn_client.handle_message = self._handle_message

    def connect(self):
        self.ttn_client.connect()

    def disconnect_and_close(self):
        self.ttn_client.disconnect_and_close()

    def _handle_message(self, rx_message):
        raise NotImplementedError("needs to be implemented by subclass")


class _SampleForwardingHandler(_NodeHandler):
    def __init__(self, ttn_client, api_root):
        super().__init__(ttn_client)
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
        logging.debug("Sample: {}".format(sample))

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
        logging.debug("Response: {}".format(response))


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


class ErsConfigurationHandler(_NodeHandler):
    """A handler for Elsys ERS devices which sends parameter downlink messages"""

    def _is_conforming(self, raw_data, mcs):
        measurement_count = len(ers.decode_payload(raw_data, dt.datetime.now()))
        logging.debug("Measurement count: %d", measurement_count)
        logging.debug("MCS: {}".format(mcs))

        protocol_payload_specification = ers.PROTOCOL_PAYLOAD_SPECIFICATION[mcs]
        expected_measurement_count = protocol_payload_specification.measurement_count

        return measurement_count == expected_measurement_count

    def _handle_message(self, rx_message):
        if not self._is_conforming(raw_data=rx_message.raw_data, mcs=rx_message.mcs):
            logging.debug("Message is not conforming to protocol payload specification")

            parameter_set = ers.PARAMETER_SETS[mcs]
            logging.debug("New parameter set: {}".format(parameter_set))

            device_id = rx_message.device_id
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
            self.ttn_client.send(device_id, tx_port, b64_payload)
        else:
            logging.debug("No change in uplink transmission parameters needed.")
