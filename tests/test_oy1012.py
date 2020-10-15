import clairttn.oy1012 as oy1012

class TestPayloadDecoding:
    def test_example(self):
        payload = bytes.fromhex("3e 44 1d 02 1b")
        co2, temperature, relative_humidity = oy1012._decode_measurement_report(payload)
        assert co2.value == 539
        assert temperature.value == 19.3
        assert relative_humidity.value == 85.1
