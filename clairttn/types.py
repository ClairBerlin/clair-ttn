from enum import Enum, unique
from collections import namedtuple
import uuid
import hashlib

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


Sample = namedtuple('Sample', [
    'timestamp',
    'co2',
    'temperature',
    'relative_humidity'],
    defaults=(None, None)
)


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
