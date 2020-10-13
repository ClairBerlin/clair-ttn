from enum import Enum, unique
import uuid
import hashlib
import datetime as dt

@unique
class LoRaWanMcs(Enum):
    """The LoRaWAN modulation and coding schemes (MCS) for EU-868 available in The Things Network."""
    SF7BW250 = 6
    SF7BW125 = 7
    SF8BW125 = 8
    SF9BW125 = 9
    SF10BW125 = 10
    SF11BW125 = 11
    SF12BW125 = 12


class DeviceUUID(uuid.UUID):
    """Convert the model-specific physical device ID into a uniform node ID.

    Different device models may have different types identifiers. For the Clair
    system to work with multiple device models, we use a uniform node
    identifier internally. Importantly, the mapping between device identifier
    and node identifier must be deterministic. For this reason, we use the
    sha256 hash function of the device identifier and the protocol name.
    """
    def __init__(self, device_id: bytes, protocol_name: str):
        hash_code = hashlib.sha256(protocol_name.encode() + device_id)
        super().__init__(bytes=hash_code.digest()[0:16])


class Sample:
    def __init__(self, timestamp, co2, temperature=None, relative_humidity=None):
        self.timestamp = timestamp
        self.co2 = co2
        self.temperature = temperature
        self.relative_humidity = relative_humidity

    def __str__(self):
        return "<Sample({ts}): co2: {co2}, temperature: {temp}: rel. humidity: {hum}>".format(
            ts = self.timestamp,
            co2 = self.co2,
            temp = self.temperature,
            hum = self.relative_humidity
        )


class Timestamp:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(dt.datetime.fromtimestamp(self.value))


class Measurement:
    def __init__(self, value):
        self.value = value


class CO2(Measurement):
    def __str__(self):
        return "{} ppm".format(self.value)


class Temperature(Measurement):
    def __str__(self):
        return "{} °C".format(self.value)


class RelativeHumidity(Measurement):
    def __str__(self):
        return "{} %".format(self.value)


class PayloadFormatException(Exception):
    pass


class PayloadContentException(Exception):
    pass
