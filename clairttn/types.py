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


# LoRaWAN data rate index for the EU 868MHz bands, following the 2015 LoRaWAN spec.
DATA_RATE_INDEX = [
    LoRaWanMcs.SF12BW125,   # data rate index 0
    LoRaWanMcs.SF11BW125,   # data rate index 1
    LoRaWanMcs.SF10BW125,   # data rate index 2
    LoRaWanMcs.SF9BW125,    # data rate index 3
    LoRaWanMcs.SF8BW125,    # data rate index 4
    LoRaWanMcs.SF7BW125,    # data rate index 5
    LoRaWanMcs.SF7BW250,    # data rate index 6
]


class DeviceUUID(uuid.UUID):
    """UUID for Clair devices

    Different device models may have different types identifiers. For the Clair
    system to work with multiple device models, we use a uniform node
    identifier internally. Importantly, the mapping between device identifier
    and node identifier must be deterministic. For this reason, we use the
    sha256 hash function of the device identifier and the protocol name.
    """

    def __init__(self, device_id: bytes, protocol_name: str):
        hash_code = hashlib.sha256(protocol_name.encode() + device_id)
        super().__init__(bytes=hash_code.digest()[0:16])


class Timestamp:
    """A point of time represented in seconds since epoch"""

    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return str(dt.datetime.fromtimestamp(self.value))


class Measurement:
    """Base class for all Clair measurements

    Attributes
    ----------
    value: float
        The value of the measurement

    """

    def __init__(self, value: float):
        self.value = value


class CO2(Measurement):
    """CO2 measurement in ppm"""

    def __str__(self):
        return "{} ppm".format(self.value)


class Temperature(Measurement):
    """Temperature measurement in °C"""

    def __str__(self):
        return "{} °C".format(self.value)


class RelativeHumidity(Measurement):
    """Relative humidity measurement in %"""

    def __str__(self):
        return "{} %".format(self.value)


class Sample:
    """A set of measurements taken at the same point of time"""

    def __init__(
        self,
        timestamp: Timestamp,
        co2: CO2,
        temperature: Temperature = None,
        relative_humidity: RelativeHumidity = None,
    ):
        self.timestamp = timestamp
        self.co2 = co2
        self.temperature = temperature
        self.relative_humidity = relative_humidity

    def __str__(self):
        return "<Sample({ts}): co2: {co2}, temperature: {temp}: rel. humidity: {hum}>".format(
            ts=self.timestamp,
            co2=self.co2,
            temp=self.temperature,
            hum=self.relative_humidity,
        )


class PayloadFormatException(Exception):
    """Exception which is thrown in case of an inadmissible payload format"""

    pass


class PayloadContentException(Exception):
    """Exception which is thrown in case of an inadmissible payload content"""

    pass
