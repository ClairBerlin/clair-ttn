import clairttn.ttn_handler as ttn_handler
import pytest


class TestTTNMessageDecoding:
    def testV3MessageWithoutPayload(self):
        app_id = "dummy"
        access_key = "dummy"
        v3_handler = ttn_handler.TtnV3Handler(app_id, access_key)

        message_without_payload = {
            "end_device_ids": {
                "device_id": "clairfeatherprotored",
                "application_ids": {"application_id": "clairchen-test"},
                "dev_eui": "9876B600001193E0",
                "join_eui": "70B3D57ED00347BA",
                "dev_addr": "260BC3D6",
            },
            "correlation_ids": [
                "as:up:01FFK0HC0MBQHSTBRW4ENBMJDS",
                "gs:conn:01FF9RMJ4AYN33YT4Q8A4K60EC",
                "gs:up:host:01FF9RMJ4KD88BFY6JV2VJY0EG",
                "gs:uplink:01FFK0HBT3ZRZGYF0M2E93CV86",
                "ns:uplink:01FFK0HBT4V6QDYZC226SATY8T",
                "rpc:/ttn.lorawan.v3.GsNs/HandleUplink:01FFK0HBT4BPHTKGRYYY9QZEWD",
                "rpc:/ttn.lorawan.v3.NsAs/HandleUplink:01FFK0HC0K767C7AG3ZJWRJ8RB",
            ],
            "received_at": "2021-09-14T20:38:54.229698936Z",
            "uplink_message": {
                "session_key_id": "AXuyqD7znKml0qbj/8Y0QQ==",
                "f_cnt": 1672,
                "rx_metadata": [
                    {
                        "gateway_ids": {
                            "gateway_id": "b827ebfffea53db3",
                            "eui": "B827EBFFFEA53DB3",
                        },
                        "time": "2021-09-14T20:56:08.912647Z",
                        "timestamp": 1036912648,
                        "rssi": -117,
                        "channel_rssi": -117,
                        "snr": -8.2,
                        "location": {
                            "latitude": 52.48299920791517,
                            "longitude": 13.361338376998903,
                            "altitude": 63,
                            "source": "SOURCE_REGISTRY",
                        },
                        "uplink_token": "Ch4KHAoQYjgyN2ViZmZmZWE1M2RiMxIIuCfr//6lPbMQiJC47gMaCwjekISKBhCup6QJIMC+veaWxkY=",
                        "channel_index": 4,
                    },
                    {
                        "gateway_ids": {
                            "gateway_id": "eui-fcc23dfffe0e316a",
                            "eui": "FCC23DFFFE0E316A",
                        },
                        "time": "2021-09-14T20:38:53.992307901Z",
                        "timestamp": 2850890604,
                        "rssi": -117,
                        "channel_rssi": -117,
                        "snr": -10.25,
                        "uplink_token": "CiIKIAoUZXVpLWZjYzIzZGZmZmUwZTMxNmESCPzCPf/+DjFqEOzGtM8KGgsI3pCEigYQ0v/lDSDgu8my/MkD",
                    },
                    {
                        "gateway_ids": {"gateway_id": "packetbroker"},
                        "packet_broker": {
                            "message_id": "01FFK0HBTHGRPQENNYGSJ7454K",
                            "forwarder_net_id": "000013",
                            "forwarder_tenant_id": "ttnv2",
                            "forwarder_cluster_id": "ttn-v2-eu-3",
                            "forwarder_gateway_eui": "C0EE40FFFF293507",
                            "forwarder_gateway_id": "eui-c0ee40ffff293507",
                            "home_network_net_id": "000013",
                            "home_network_tenant_id": "ttn",
                            "home_network_cluster_id": "ttn-eu1",
                        },
                        "rssi": -119,
                        "channel_rssi": -119,
                        "snr": -9.5,
                        "location": {
                            "latitude": 52.48453486,
                            "longitude": 13.34653402,
                            "altitude": 46,
                        },
                        "uplink_token": "eyJnIjoiWlhsS2FHSkhZMmxQYVVwQ1RWUkpORkl3VGs1VE1XTnBURU5LYkdKdFRXbFBhVXBDVFZSSk5GSXdUazVKYVhkcFlWaFphVTlwU2xkUmJYaEhWRmMwZUdKcVNucFdXRkpLVjIwMVRFbHBkMmxrUjBadVNXcHZhV0ZWTVcxUmExcDRUakI0UzFkdFpHNWtWbFpQVlcxc2RWUnVXblpWVTBvNUxtSlZWM1p4WW5KbGFtcFRabXN4UlZJMGJ6bDJZM2N1V0ZwcFZYRjFSRFpPYldSR09XZEdaQzVYV1hobVIyNUpXVGxwVDJsclRUTTFVRk51TlRabVZGOTRURlJoTlRsTFpUbExYelI1V0V4TlNqZDBNRkJOU21wdFMxcE1VbkJhTUU5d056UTJPVTlITVMxWGVqUjFkeTB6Wm05V1prNW1Va3BrZUZKdE4zZHRVMEprTm5ab1JGTkhhSE50WVZCcVFrNXJhM1o0WDJKaU5qWk9ibDh5T1RCMllVbDBNREJCVVVVNWNuTjBhbFpzYkhsU2FFeHFWM0JRUmpWWlpWUlRTM1pWVEdsWFRIWlZSRzlpVEhOcWRuWnNaeTVZZFdjek9UQlRWVjlVWjNaWVNXeGpiV052WjJGbiIsImEiOnsiZm5pZCI6IjAwMDAxMyIsImZ0aWQiOiJ0dG52MiIsImZjaWQiOiJ0dG4tdjItZXUtMyJ9fQ==",
                    },
                ],
                "settings": {
                    "data_rate": {"lora": {"bandwidth": 125000, "spreading_factor": 9}},
                    "data_rate_index": 3,
                    "coding_rate": "4/5",
                    "frequency": "867300000",
                    "timestamp": 1036912648,
                    "time": "2021-09-14T20:56:08.912647Z",
                },
                "received_at": "2021-09-14T20:38:54.020897204Z",
                "consumed_airtime": "0.164864s",
                "network_ids": {
                    "net_id": "000013",
                    "tenant_id": "ttn",
                    "cluster_id": "ttn-eu1",
                },
            },
        }

        rx_message = v3_handler._extract_rx_message(message_without_payload)

        assert rx_message is None
