from clairttn.types import *
import datetime as dt
from collections import namedtuple
import typing


class ClairchenDeviceUUID(DeviceUUID):
    """UUID for Clairchen devices"""

    def __init__(self, device_id: bytes):
        super().__init__(device_id, "CLAIRCHEN")


def decode_payload(payload: bytes, rx_datetime: dt.datetime, mcs: LoRaWanMcs) -> typing.List[Sample]:
    """Decode a Clairchen uplink payload and return a list of samples."""

    measurements = _decode_measurements(payload)
    samples = _to_samples(measurements, rx_datetime, mcs)
    return samples


PayloadInfo = namedtuple('PayloadInfo', [
    'airtime',
    'measurement_count',
    'measurement_interval'])


PROTOCOL_PAYLOAD_SPECIFICATION = {
    LoRaWanMcs.SF7BW250: PayloadInfo(
        airtime=0.0257,
        measurement_count=2,
        measurement_interval=38),
    LoRaWanMcs.SF7BW125: PayloadInfo(
        airtime=0.0515,
        measurement_count=2,
        measurement_interval=75),
    LoRaWanMcs.SF8BW125: PayloadInfo(
        airtime=0.0927,
        measurement_count=2,
        measurement_interval=134),
    LoRaWanMcs.SF9BW125: PayloadInfo(
        airtime=0.1853,
        measurement_count=3,
        measurement_interval=178),
    LoRaWanMcs.SF10BW125: PayloadInfo(
        airtime=0.3707,
        measurement_count=5,
        measurement_interval=214),
    LoRaWanMcs.SF11BW125: PayloadInfo(
        airtime=0.7414,
        measurement_count=4,
        measurement_interval=534),
    LoRaWanMcs.SF12BW125: PayloadInfo(
        airtime=1.4828,
        measurement_count=5,
        measurement_interval=855)
}


def _decode_measurements(data: bytes):
    version, message_id, message_header, data = _decode_header(data)

    if version != 0:
        raise PayloadContentException("unsupported version number: {}".format(version))

    if message_id != 0:
        raise PayloadContentException("unsupported message id: {}".format(message_id))

    sample_count = message_header + 1

    measurements = _decode_sample_bytes(data)
    if len(measurements) != sample_count:
        raise PayloadContentException("incorrect sample count: {}".format(sample_count))

    return measurements


def _to_samples(measurements: typing.List[typing.Dict], rx_datetime: dt.datetime, mcs: LoRaWanMcs):
    measurement_interval = PROTOCOL_PAYLOAD_SPECIFICATION[mcs].measurement_interval
    rx_timestamp = round(rx_datetime.timestamp())
    sample_count = len(measurements)

    samples = [
        Sample(
            timestamp = Timestamp(rx_timestamp - (sample_count - i - 1) * measurement_interval),
            co2 = measurement['co2'],
            temperature = measurement['temperature'],
            relative_humidity = measurement['relative_humidity']
        ) for i, measurement in enumerate(measurements)
    ]

    return samples


def _decode_header(data: bytes):
    header_byte = data[0]
    remaining_data = data[1:]

    version = (header_byte & 0b11000000) >> 6
    message_id = (header_byte & 0b00111000) >> 3
    message_header = header_byte & 0b00000111

    return (version, message_id, message_header, remaining_data)


def _decode_sample_bytes(data: bytes):
    measurements = []

    while data:
        co2, temperature, humidity, data = _decode_sample(data)
        measurements.append({
            'co2': co2,
            'temperature': temperature,
            'relative_humidity': humidity
        })

    return measurements


def _decode_sample(data: bytes):
    if len(data) < 2:
        raise PayloadFormatException("inadmissible number of sample bytes: {}".format(len(data)))

    remaining_data = data[2:]

    co2_value = int.from_bytes(data[0:1], byteorder='big')
    co2_value *= 20

    temp_hum_int = int.from_bytes(data[1:2], byteorder='big')
    temp_value = (temp_hum_int & 0b11111000) >> 3
    hum_value = ((temp_hum_int & 0b111) * 10) + 10

    return (CO2(co2_value), Temperature(temp_value), RelativeHumidity(hum_value), remaining_data)
