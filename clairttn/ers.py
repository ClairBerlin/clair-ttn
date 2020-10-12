from clairttn.types import *
from collections import namedtuple

def decode_payload(payload, rx_datetime):
    """Decode an ERS uplink payload and return a list of samples.

        Parameters:
            payload (bytes)         : the uplink payoad
            rx_datetime (datetime)  : the reception time of the message

        Returns:
            samples (list[Sample])  : the list of samples
    """

    measurements = _decode_measurements(payload)
    samples = _to_samples(measurements, rx_datetime)

    return samples


PayloadInfo = namedtuple('PayloadInfo', [
    'airtime',
    'measurement_count',
    'measurement_interval'])


PROTOCOL_PAYLOAD_SPECIFICATION = {
    LoRaWanMcs.SF7BW250: PayloadInfo(
        airtime=0.033408,
        measurement_count=2,
        measurement_interval=326),
    LoRaWanMcs.SF7BW125: PayloadInfo(
        airtime=0.066816,
        measurement_count=2,
        measurement_interval=326),
    LoRaWanMcs.SF8BW125: PayloadInfo(
        airtime=0.123392,
        measurement_count=2,
        measurement_interval=326),
    LoRaWanMcs.SF9BW125: PayloadInfo(
        airtime=0.226304,
        measurement_count=2,
        measurement_interval=326),
    LoRaWanMcs.SF10BW125: PayloadInfo(
        airtime=0.370688,
        measurement_count=3,
        measurement_interval=356),
    LoRaWanMcs.SF11BW125: PayloadInfo(
        airtime=0.823296,
        measurement_count=4,
        measurement_interval=593),
    LoRaWanMcs.SF12BW125: PayloadInfo(
        airtime=1.646592,
        measurement_count=5,
        measurement_interval=948)
}


ErsParameterSet = namedtuple('ErsParameterSet', [
    'sampling_period',
    'temperature_period',
    'send_period'
])


ERS_PARAMETER_SETS = {
    mcs: ErsParameterSet(
        sampling_period = PROTOCOL_PAYLOAD_SPECIFICATION[mcs].measurement_interval,
        temperature_period = 1 if mcs.value < LoRaWanMcs.SF10BW125.value else 0,
        send_period = PROTOCOL_PAYLOAD_SPECIFICATION[mcs].measurement_count
    )
    for mcs in LoRaWanMcs
}


def encode_parameter_set(parameter_set):
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


def _decode_measurements(data):
    measurements = []

    while data:
        measurement, data = _decode_sensor_data(data)
        measurements.append(measurement)

    return measurements


def _to_samples(measurements, rx_datetime):
    # Let's check the payload's content:
    # ERS payloads must contain CO2 measurements.
    # The number of CO2 measurements must be conforming to the payload spec.
    # They may contain temperature and humidity.
    # The number of temperature and humidity measurements is either 0 or equal
    # to the number of CO2 measurements.
    # All measurements are sorted in reverse-chronological order (LIFO).
    # The order within a CO2/temperature/humidity sample group does not matter.
    # This is ok: [C, T, H, H, T, C, T, H, C]
    # This is inadmissible: [C, C, C, T, T, T, H, H, H]
    sample_count = len([m for m in measurements if type(m) == CO2])
    valid_sample_counts = {ps.measurement_count for ps in PROTOCOL_PAYLOAD_SPECIFICATION.values()}
    if not sample_count in valid_sample_counts:
        raise PayloadContentException("invalid number of measurements samples: {}".format(sample_count))

    # number of measurements per sample group, either 1 or 3
    n = int(len(measurements) / sample_count)
    if n != 1 and n != 3:
        raise PayloadContentException("invalid number of measurements: {}".format(len(measurements)))

    # split measurements in sub lists of equal size n
    sample_groups = [measurements[i:i+n] for i in range(0, len(measurements), n)]

    # check for exactly one CO2 measurement in each sample group
    if not all([len([m for m in sg if type(m) == CO2]) == 1 for sg in sample_groups]):
        raise PayloadContentException("invalid order of measurements")

    # check for either exactly one or zero temperature/humidity measurement
    t_counts = [len([m for m in sg if type(m) == Temperature]) for sg in sample_groups]
    h_counts = [len([m for m in sg if type(m) == RelativeHumidity]) for sg in sample_groups]
    if not ((all([c == 1 for c in t_counts]) and all([c == 1 for c in h_counts])) or \
            (all([c == 0 for c in t_counts]) and all([c == 0 for c in h_counts]))):
        raise PayloadContentException("invalid combination of measurements")

    rx_timestamp = round(rx_datetime.timestamp())
    # the measurement interval is determined by the number of samples per message
    measurement_interval = next(ps.measurement_interval for ps in PROTOCOL_PAYLOAD_SPECIFICATION.values() \
                                if ps.measurement_count == sample_count)

    samples = [
        Sample(
            timestamp = rx_timestamp - i * measurement_interval,
            co2 = next(m for m in sg if type(m) == CO2),
            temperature = next((m for m in sg if type(m) == Temperature), None),
            relative_humidity = next((m for m in sg if type(m) == RelativeHumidity), None)
        ) for i, sg in enumerate(sample_groups)
    ]

    return samples


def _decode_sensor_data(data):
    # ignoring nob, which should be 0
    __, sensor_type, data = _decode_sensor_type(data)
    return _DATA_DECODING_FUNCTIONS[sensor_type](data)


def _decode_sensor_type(data):
    header = data[0]
    remaining_data = data[1:]

    # nob, number of offset bytes
    nob = (header & 0b11000000) >> 6
    if nob:
        error = "nob {} != 0 not allowed for Clair ERS sensors".format(nob)
        raise PayloadContentException(error)

    sensor_type = header & 0b00111111
    if sensor_type not in _DATA_DECODING_FUNCTIONS:
        raise PayloadContentException("unsupported sensor type: {}".format(sensor_type))

    return (nob, sensor_type, remaining_data)


def _decode_temperature(data):
    if len(data) < 2:
        raise PayloadFormatException("less than two bytes to decode temperature")

    temperature_bytes = data[0:2]
    remaining_data = data[2:]

    temperature_value = int.from_bytes(temperature_bytes, byteorder='big', signed=True) / 10
    if temperature_value < -3276.5 or temperature_value > 3276.5:
        raise PayloadContentException("temperature {} not in admissible range")

    temperature = Temperature(temperature_value)

    return (temperature, remaining_data)


def _decode_humidity(data):
    if not data:
        raise PayloadFormatException("no byte to decode relative humidity")

    humidity_value = data[0]
    remaining_data = data[1:]

    if humidity_value > 100:
        raise PayloadContentException("relative humidity {} > 100".format(humidity_value))

    humidity = RelativeHumidity(humidity_value)

    return (humidity, remaining_data)


def _decode_co2(data):
    if len(data) < 2:
        raise PayloadFormatException("less than two bytes to decode co2")

    co2_bytes = data[0:2]
    remaining_data = data[2:]

    co2_value = int.from_bytes(co2_bytes, byteorder='big')
    if co2_value > 10000:
        raise PayloadContentException("co2 {} > 10000".format(co2_value))

    co2 = CO2(co2_value)

    return (co2, remaining_data)


_DATA_DECODING_FUNCTIONS = {
    0x01: _decode_temperature,
    0x02: _decode_humidity,
    0x06: _decode_co2
}


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
