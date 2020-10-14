import clairttn.clairchen as clairchen
import clairttn.types as types
import datetime as dt
import pytest


class TestHeaderDecoding:
    def test_decode_v0(self):
        version, message_id, message_header, __ = clairchen._decode_header(bytes.fromhex('03'))
        assert version == 0
        assert message_id == 0
        assert message_header == 3

    def test_decode_v1(self):
        version, message_id, message_header, __ = clairchen._decode_header(bytes.fromhex('41'))
        assert version == 1
        assert message_id == 0
        assert message_header == 1

    def test_decode_id2(self):
        version, message_id, message_header, __ = clairchen._decode_header(bytes.fromhex('12'))
        assert version == 0
        assert message_id == 2
        assert message_header == 2


class TestMeasurementsDecoding:
    def test_inadmissible_version(self):
        with pytest.raises(types.PayloadContentException):
            clairchen._decode_measurements(bytes.fromhex("41"))

    def test_inadmissible_type(self):
        with pytest.raises(types.PayloadContentException):
            clairchen._decode_measurements(bytes.fromhex("12"))

    def test_payload(self):
        payload = bytes.fromhex('02 1B E4 1A E4 19 E3')
        measurements = clairchen._decode_measurements(payload)
        assert len(measurements) == 3
        measurement = measurements[1]
        assert measurement['co2'].value == 520
        assert measurement['temperature'].value == 28
        assert measurement['relative_humidity'].value == 50


class TestSampleDecoding:
    def test_correct_encodings(self):
        EXPECTED_SAMPLE_RESULT = {
            bytes.fromhex('00 00'): (0, 0, 10),
            bytes.fromhex('00 04'): (0, 0, 50),
            bytes.fromhex('00 07'): (0, 0, 80),
            bytes.fromhex('00 80'): (0, 16, 10),
            bytes.fromhex('00 B0'): (0, 22, 10),
            bytes.fromhex('00 50'): (0, 10, 10),
            bytes.fromhex('00 F8'): (0, 31, 10),
            bytes.fromhex('01 00'): (20, 0, 10),
            bytes.fromhex('32 00'): (1000, 0, 10),
            bytes.fromhex('64 00'): (2000, 0, 10),
            bytes.fromhex('7D 00'): (2500, 0, 10)
        }

        for data, expected_result in EXPECTED_SAMPLE_RESULT.items():
            co2, temperature, humidity, data = clairchen._decode_sample(data)
            assert co2.value == expected_result[0]
            assert temperature.value == expected_result[1]
            assert humidity.value == expected_result[2]
            assert len(data) == 0

    def test_samplefail(self):
        with pytest.raises(types.PayloadFormatException):
            clairchen._decode_sample(bytes.fromhex('80'))
            clairchen._decode_sample(bytes.fromhex('80 10 80'))


class TestPayloadDecoding:
    def test_timestamps(self):
        payload = bytes.fromhex('02 1B E4 1A E4 19 E3')
        rx_time = dt.datetime.fromisoformat("2020-09-01 13:17:31+00:00")
        mcs = types.LoRaWanMcs.SF9BW125
        samples = clairchen.decode_payload(payload, rx_time, mcs)
        assert len(samples) == 3
        assert samples[0].timestamp.value == 1598966251 - 2 * 178
        assert samples[1].timestamp.value == 1598966251 - 178
        assert samples[2].timestamp.value == 1598966251
