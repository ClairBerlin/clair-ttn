import clairttn.talkpool as tp

class TestPayloadDecoding:
    def test_example(self):
        payload = bytes.fromhex("3e 44 1d 02 1b")
        co2, temperature, relative_humidity = tp._decode_measurement_report(payload)
        assert co2.value == 539
        assert temperature.value == 19.3
        assert relative_humidity.value == 85.1
