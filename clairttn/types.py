from enum import Enum, unique
from collections import namedtuple

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
