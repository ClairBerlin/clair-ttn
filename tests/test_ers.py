# from clairttners.handler import ERS_PARAMETER_SETS, _encode_parameter_set
# from clairserver.ingestair.ttn.lorawandefinitions import LoRaWanMcs
import clairttn.ers as ers
import clairttn.types as types
import datetime as dt
import pytest


def _assert_is_co2_equal_to(result, value):
    assert isinstance(result, types.CO2)
    assert result.value == value


class TestCo2Decoding:
    def test_co2_ok(self):
        result, __ = ers._decode_co2(bytes.fromhex("01 C2"))
        _assert_is_co2_equal_to(result, 450)

    def test_co2_max(self):
        result, __ = ers._decode_co2(bytes.fromhex("27 10"))
        _assert_is_co2_equal_to(result, 10000)

    def test_co2_min(self):
        result, __ = ers._decode_co2(bytes.fromhex("00 00"))
        _assert_is_co2_equal_to(result, 0)

    def test_co2_too_short(self):
        with pytest.raises(types.PayloadFormatException):
            ers._decode_co2(bytes.fromhex("2E"))

    def test_co2_to_carbonized(self):
        with pytest.raises(types.PayloadContentException):
            ers._decode_co2(bytes.fromhex("27 11"))



def _assert_is_temperature_approx_equal_to(result, value):
    assert isinstance(result, types.Temperature)
    assert result.value == pytest.approx(value, 0.01)


class TestTemperatureDecoding:
    def test_temp_positive(self):
        result, __ = ers._decode_temperature(bytes.fromhex("00 64"))
        _assert_is_temperature_approx_equal_to(result, 10.0)

    def test_temp_min(self):
        result, __ = ers._decode_temperature(bytes.fromhex("80 03"))
        _assert_is_temperature_approx_equal_to(result, -3276.5)

    def test_temp_max(self):
        result, __ = ers._decode_temperature(bytes.fromhex("7F FD"))
        _assert_is_temperature_approx_equal_to(result, 3276.5)

    def test_too_short(self):
        with pytest.raises(types.PayloadFormatException):
            ers._decode_temperature(bytes.fromhex("00"))

    def test_too_hot(self):
        with pytest.raises(types.PayloadContentException):
            ers._decode_temperature(bytes.fromhex("7F FE"))


def _assert_is_rel_humidity_equal_to(result, value):
    assert isinstance(result, types.RelativeHumidity)
    assert result.value == value


class TestRelativeHumidityDecoding:
    def test_rh_ok(self):
        result, __ = ers._decode_humidity(bytes.fromhex("37"))
        _assert_is_rel_humidity_equal_to(result, 55)

    def test_rh_max(self):
        result, __ = ers._decode_humidity(bytes.fromhex("64"))
        _assert_is_rel_humidity_equal_to(result, 100)

    def test_rh_min(self):
        result, __ = ers._decode_humidity(bytes.fromhex("00"))
        _assert_is_rel_humidity_equal_to(result, 0)

    def test_rh_too_short(self):
        with pytest.raises(types.PayloadFormatException):
            ers._decode_humidity(b'')

    def test_rh_too_humid(self):
        with pytest.raises(types.PayloadContentException):
            ers._decode_humidity(bytes.fromhex('FF'))


class TestMeasurementsDecoding:
    def test_multi_co2_decoding(self):
        payload = bytes.fromhex("06 00 CD 06 00 CE 06 00 CF")
        measurements = ers._decode_measurements(payload)
        assert len(measurements) == 3
        for m in measurements:
            assert isinstance(m, types.CO2)
        assert [m.value for m in measurements] == [205, 206, 207]

    def test_multi_value_decoding(self):
        # Two three-value measurements.
        payload = bytes.fromhex("01 00 CD 02 50 06 03 FA 01 00 CE 02 60 06 03 FF")
        measurements = ers._decode_measurements(payload)
        assert len(measurements) == 6
        assert [type(m) for m in measurements] == [
            types.Temperature,
            types.RelativeHumidity,
            types.CO2,
            types.Temperature,
            types.RelativeHumidity,
            types.CO2
        ]
        assert [m.value for m in measurements] == [20.5, 80, 1018, 20.6, 96, 1023]

    def test_incomplete(self):
        # a header without data
        payload = bytes.fromhex("06")
        with pytest.raises(types.PayloadFormatException):
            ers._decode_measurements(payload)


class TestSampleConstruction:
    def test_two_samples(self):
        payload = bytes.fromhex("01 00 C4 02 34 06 03 54 01 00 C4 02 34 06 03 5F")
        samples = ers.decode_payload(payload, dt.datetime.now())
        assert len(samples) == 2

    def test_no_co2(self):
        # two measurements without CO2-values
        payload = bytes.fromhex("01 00 CD 02 50 01 00 CE 02 60")
        with pytest.raises(types.PayloadContentException):
            measurements = ers._decode_measurements(payload)
            ers._to_samples(measurements, dt.datetime.now())

    def test_inconsistent_measurements(self):
        # CO2-temperature, followed by CO2-humidity
        payload = bytes.fromhex("01 00 CD 06 03 FA 02 60 06 03 FF")
        with pytest.raises(types.PayloadContentException):
            measurements = ers._decode_measurements(payload)
            ers._to_samples(measurements, dt.datetime.now())

    def test_no_measurements(self):
        payload: bytes = b''
        with pytest.raises(types.PayloadContentException):
            measurements = ers._decode_measurements(payload)
            ers._to_samples(measurements, dt.datetime.now())


# generated using the ELSYS Downlink Generator
# https://www.elsys.se/en/downlink-generator/
# according to
# https://docs.google.com/spreadsheets/d/1oWVQ4jNrC2VMZ8UkpnLZMsMh9QyX5it7FH3Bk12c-1E/edit#gid=0
EXPECTED_ENCODINGS = {
    types.LoRaWanMcs.SF12BW125: bytes.fromhex('3E0F14000003B415000000001F00000005'),
    types.LoRaWanMcs.SF11BW125: bytes.fromhex('3E0F140000025115000000001F00000004'),
    types.LoRaWanMcs.SF10BW125: bytes.fromhex('3E0F140000016415000000001F00000003'),
    types.LoRaWanMcs.SF9BW125: bytes.fromhex('3E0F140000014615000000011F00000002'),
    types.LoRaWanMcs.SF8BW125: bytes.fromhex('3E0F140000014615000000011F00000002'),
    types.LoRaWanMcs.SF7BW125: bytes.fromhex('3E0F140000014615000000011F00000002'),
    types.LoRaWanMcs.SF7BW250: bytes.fromhex('3E0F140000014615000000011F00000002')
}

def test_parameter_set_encodings():
    for mcs in types.LoRaWanMcs:
        parameter_set = ers.PARAMETER_SETS[mcs]
        assert(ers.encode_parameter_set(parameter_set) == EXPECTED_ENCODINGS[mcs])
