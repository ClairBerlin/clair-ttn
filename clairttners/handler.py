import ttn
import logging
import base64
from typing import NamedTuple
from clairserver.ingestair.ttn.elsys.ersprotocol_v0 import ElSysErsProtocol
from clairserver.ingestair.ttn.lorawandefinitions import LoRaWanMcs

ErsParameterSet = NamedTuple('ErsParameterSet', [
    ('sampling_period', int),
    ('temperature_period', int),
    ('send_period', int)
])

ERS_PARAMETER_SETS = {
    mcs: ErsParameterSet(
        sampling_period = ElSysErsProtocol.PROTOCOL_PAYLOAD_SPECIFICATION[mcs].measurement_interval,
        temperature_period = 1 if mcs.value < LoRaWanMcs.SF10BW125.value else 0,
        send_period = ElSysErsProtocol.PROTOCOL_PAYLOAD_SPECIFICATION[mcs].measurement_count
    )
    for mcs in LoRaWanMcs
}

class Handler:
    def __init__(self, app_id, access_key):
        logging.debug("app id: {}".format(app_id))
        ttnHandler = ttn.HandlerClient(app_id, access_key)
        self._mqtt_client = ttnHandler.data()

        def _configure_if_not_conforming_to_spec(message, client):
            logging.debug("uplink message received from {}".format(message.dev_id))
            logging.debug(str(message))

            if not _is_message_conforming_to_spec(message):
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

        self._mqtt_client.set_uplink_callback(_configure_if_not_conforming_to_spec)

    def connect(self):
        self._mqtt_client.connect()

    def close(self):
        self._mqtt_client.close()

def _is_message_conforming_to_spec(message):
    pdu = base64.b64decode(message.payload_raw)
    logging.debug("decoded payload: {}".format(pdu.hex('-').upper()))

    measurement_count = len(ElSysErsProtocol.decode_pdu(pdu))
    logging.debug("measurement count: {}".format(measurement_count))

    if not (hasattr(message, 'metadata') and hasattr(message.metadata, 'data_rate')):
        logging.warning("message without data_rate, assuming simulated uplink message")
        return True

    mcs = LoRaWanMcs[message.metadata.data_rate]
    logging.debug("mcs: {}".format(mcs))

    protocol_payload_specification = ElSysErsProtocol.PROTOCOL_PAYLOAD_SPECIFICATION[mcs]
    expected_measurement_count = protocol_payload_specification.measurement_count

    return measurement_count == expected_measurement_count

def _encode_parameter_set(parameter_set):
    payload = bytearray()

    header = b'\x3E' # always 0x3E
    payload.extend(header)

    sampling_period_data = _encode_sampling_period(parameter_set.sampling_period)
    temperature_period_data = _encode_temperature_period(parameter_set.temperature_period)
    send_period_data = _encode_send_period(parameter_set.send_period)

    length = len(sampling_period_data) + len(temperature_period_data) + len(send_period_data)
    payload.extend(length.to_bytes(1, byteorder='big'))

    payload.extend(sampling_period_data)
    payload.extend(temperature_period_data)
    payload.extend(send_period_data)

    return payload

def _encode_sampling_period(sampling_period):
    sampling_period_data = bytearray(b'\x14')
    sampling_period_data.extend(sampling_period.to_bytes(4, byteorder='big'))
    return sampling_period_data

def _encode_temperature_period(temperature_period):
    temperature_period_data = bytearray(b'\x15')
    temperature_period_data.extend(temperature_period.to_bytes(4, byteorder='big'))
    return temperature_period_data

def _encode_send_period(send_period):
    send_period_data = bytearray(b'\x1F')
    send_period_data.extend(send_period.to_bytes(4, byteorder='big'))
    return send_period_data
