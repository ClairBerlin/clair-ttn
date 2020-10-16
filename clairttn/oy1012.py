import datetime as dt
from collections import namedtuple
import typing
import clairttn.types as t


class Oy1012DeviceUUID(t.DeviceUUID):
    """UUID for Talkpool OY1012 devices"""

    def __init__(self, device_id: bytes):
        super().__init__(device_id, "TALKPOOLOY1012")


def decode_payload(payload: bytes, rx_datetime: dt.datetime) -> typing.List[t.Sample]:
    """Decode a Talkpool uplink payload and return a list of samples.

    Talkpool devices send single measurement tuples only.
    """

    co2, temperature, relative_humidity = _decode_measurement_report(payload)

    return [
        t.Sample(
            timestamp = t.Timestamp(round(rx_datetime.timestamp())),
            co2 = co2,
            temperature = temperature,
            relative_humidity = relative_humidity
        )
    ]


def _decode_measurement_report(data: bytes):
    temp_bytes = bytearray.fromhex("00 00")
    temp_bytes[1] |= (data[2] & 0xF0) >> 4
    temp_bytes[1] |= (data[0] << 4) & 0xF0
    temp_bytes[0] |= data[0] >> 4

    temp_value = int.from_bytes(temp_bytes, byteorder='big')
    temp_value -= 800
    temp_value /= 10

    hum_bytes = bytearray.fromhex("00 00")
    hum_bytes[1] |= data[2] & 0x0F
    hum_bytes[1] |= (data[1] << 4) & 0xF0
    hum_bytes[0] |= data[1] >> 4

    hum_value = int.from_bytes(hum_bytes, byteorder='big')
    hum_value -= 250
    hum_value /= 10

    co2_value = int.from_bytes(data[3:5], byteorder='big')

    return (t.CO2(co2_value), t.Temperature(temp_value), t.RelativeHumidity(hum_value))
