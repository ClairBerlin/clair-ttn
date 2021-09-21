import clairttn.ttn_handler as ttn_handler
import pytest
import base64
import dateutil.parser as dtparser


class TestTTNMessageDecoding:
    def testRegularUplinkMessage(self):
        app_id = "dummy"
        access_key = "dummy"
        v3_handler = ttn_handler.TtnV3Handler(app_id, access_key)

        regular_message = {
            "end_device_ids": {
                "device_id": "clairfeatherprotored",
                "application_ids": {"application_id": "clairchen-test"},
                "dev_eui": "9876B600001193E0",
                "join_eui": "70B3D57ED00347BA",
                "dev_addr": "260BC3D6",
            },
            "correlation_ids": [
                "as:up:01FG1JPY8VGZWRTHPJGY4Y41VM",
                "ns:uplink:01FG1JPY2DYSQ25A54MTNHWRXZ",
                "pba:conn:up:01FG16560GWJ3GWMXXXEH02WCH",
                "pba:uplink:01FG1JPY2AJ2PQ0YCFKYT6ZGXF",
                "rpc:/ttn.lorawan.v3.GsNs/HandleUplink:01FG1JPY2DSWV5XCSEJ1M92T4J",
                "rpc:/ttn.lorawan.v3.NsAs/HandleUplink:01FG1JPY8VY8M6M3FH1RH5MJQ0",
            ],
            "received_at": "2021-09-20T12:25:53.180595270Z",
            "uplink_message": {
                "session_key_id": "AXuyqD7znKml0qbj/8Y0QQ==",
                "f_port": 1,
                "f_cnt": 2621,
                "frm_payload": "Aie0KLQotA==",
                "rx_metadata": [
                    {
                        "gateway_ids": {"gateway_id": "packetbroker"},
                        "packet_broker": {
                            "message_id": "01FG1JPY2AJ2PQ0YCFKYT6ZGXF",
                            "forwarder_net_id": "000013",
                            "forwarder_tenant_id": "ttnv2",
                            "forwarder_cluster_id": "ttn-v2-eu-3",
                            "forwarder_gateway_eui": "C0EE40FFFF293507",
                            "forwarder_gateway_id": "eui-c0ee40ffff293507",
                            "home_network_net_id": "000013",
                            "home_network_tenant_id": "ttn",
                            "home_network_cluster_id": "ttn-eu1",
                        },
                        "rssi": -121,
                        "channel_rssi": -121,
                        "snr": -10.2,
                        "location": {
                            "latitude": 52.48453486,
                            "longitude": 13.34653402,
                            "altitude": 46,
                        },
                        "uplink_token": "eyJnIjoiWlhsS2FHSkhZMmxQYVVwQ1RWUkpORkl3VGs1VE1XTnBURU5LYkdKdFRXbFBhVXBDVFZSSk5GSXdUazVKYVhkcFlWaFphVTlwU1RCU1Z6RXdaVzEwWVZOc2FIWlhWRVpHVVd0d05FbHBkMmxrUjBadVNXcHZhVlJJU2paaWJFSnhZV3hrTlUxc1pGWlJNMEpWVDFWS1JWUXlaRUprZVVvNUxtTjVWbGt6Y3pocmJGZFdja1pYTjJsVGJXUnZkMmN1T1VocmNYRjVWbk5ZVVZsTVh6SkNXaTVOV1dGblQwWkRUMkpUU1VodWQwTkZjMUZ3VUZseVprNVVXRlZvVVZSWlJVeFhVM3BoVWswM01qZEhWa016ZEhOdWJqVnhVV2RSVlVKRk5WUlFTVWR1VkdwbFJHMVVTVEJhVUVFelRWVmFkV0kxU1VWUE5qaHJSemM0ZDJsSVNEQTRXRTVvVTNoa01VaFBVako1ZVY5cFNFOUZOMjFGTW5BNVEzcHlXa1owZDNscVdTMXhUamhXUTE5aU1rYzNVVE5FVEMxVk1XOHhhazFYTFRkVlZsOU1aVGswY0VGSlpFbFNVVWRHVVRSbkxsQjJORXRCT0RJMlpFOUNXSFpzU0hFNFUyRlhZVkU9IiwiYSI6eyJmbmlkIjoiMDAwMDEzIiwiZnRpZCI6InR0bnYyIiwiZmNpZCI6InR0bi12Mi1ldS0zIn19",
                    }
                ],
                "settings": {
                    "data_rate": {"lora": {"bandwidth": 125000, "spreading_factor": 9}},
                    "data_rate_index": 3,
                    "coding_rate": "4/5",
                    "frequency": "867100000",
                },
                "received_at": "2021-09-20T12:25:52.973476075Z",
                "consumed_airtime": "0.185344s",
                "network_ids": {
                    "net_id": "000013",
                    "tenant_id": "ttn",
                    "cluster_id": "ttn-eu1",
                },
            },
        }

        rx_message = v3_handler._extract_rx_message(regular_message)

        assert rx_message.device_eui == bytearray.fromhex("9876B600001193E0")
        assert rx_message.device_id == "clairfeatherprotored"
        assert rx_message.raw_data == base64.b64decode("Aie0KLQotA==")
        assert rx_message.rx_datetime == dtparser.parse(
            "2021-09-20T12:25:52.973476075Z"
        )
        assert rx_message.rx_port == 1

    def testV3MessageWithoutLoraRate(self):
        app_id = "dummy"
        access_key = "dummy"
        v3_handler = ttn_handler.TtnV3Handler(app_id, access_key)

        message_without_rate = {
            "end_device_ids": {
                "device_id": "66b8ccaa-90b9-2d24-bf59-0ea9e23b3bb4",
                "application_ids": {"application_id": "elsys-ers-co2"},
                "dev_eui": "A81758FFFE053C84",
                "join_eui": "70B3D57ED0035B40",
                "dev_addr": "260B530E",
            },
            "correlation_ids": [
                "as:up:01FG3YTC0K0KPEFA5FDKCZKF8E",
                "ns:uplink:01FG3YTBT578KF54GBQ4F4071G",
                "pba:conn:up:01FG2QC930NHK24X1NYE3VRZPB",
                "pba:uplink:01FG3YTBSMERJP80229JDGN90N",
                "rpc:/ttn.lorawan.v3.GsNs/HandleUplink:01FG3YTBT5NG4T0CKD8CH6WSFN",
                "rpc:/ttn.lorawan.v3.NsAs/HandleUplink:01FG3YTC0J0H7ZVCQB0YWZ3FKP",
            ],
            "received_at": "2021-09-21T10:35:57.332885835Z",
            "uplink_message": {
                "session_key_id": "AXwFUO6mb0zrxADfwled5Q==",
                "f_port": 5,
                "f_cnt": 41,
                "frm_payload": "BgLHBgKrBgL6",
                "decoded_payload": {"co2": 762},
                "rx_metadata": [
                    {
                        "gateway_ids": {"gateway_id": "packetbroker"},
                        "packet_broker": {
                            "message_id": "01FG3YTBSMERJP80229JDGN90N",
                            "forwarder_net_id": "000013",
                            "forwarder_tenant_id": "ttnv2",
                            "forwarder_cluster_id": "ttn-v2-eu-4",
                            "forwarder_gateway_eui": "7276FF000B030C96",
                            "forwarder_gateway_id": "eui-7276ff000b030c96",
                            "home_network_net_id": "000013",
                            "home_network_tenant_id": "ttn",
                            "home_network_cluster_id": "ttn-eu1",
                        },
                        "rssi": -119,
                        "channel_rssi": -119,
                        "snr": -15.5,
                        "location": {
                            "latitude": 52.52603005,
                            "longitude": 13.31433411,
                            "altitude": 65,
                        },
                        "uplink_token": "eyJnIjoiWlhsS2FHSkhZMmxQYVVwQ1RWUkpORkl3VGs1VE1XTnBURU5LYkdKdFRXbFBhVXBDVFZSSk5GSXdUazVKYVhkcFlWaFphVTlwU2toT1Z6RjZaV3R2TkU5SGNEUmtNVnB4WkdwQ1ZrbHBkMmxrUjBadVNXcHZhV1F3V2t0VFdFWlZXVEZhTkZSNlZUUmpXR1J0Wkc1a05sTnRXVE5rZVVvNUxteDZMVnBIYlY5VkxXTkhUMjg0U1MxbWVuVmpZVUV1V21abldERk9NbFV5ZGxOT00zbGxOUzVhTlcwMlVtUjBibUpsYlZrNVVsa3hiVEpITTBkTWFrWmtVRzUzYlZkWVZYVTFialJrZFc5YVFtUnlObFJLV25aUFUyTlRiVEIwVlRGU1dWSnJUVlpuVjBOM01HaG5ORzQwUjBaWFZVa3pZbEptVkZOaFZucGpWamhXTVdWUlMweHVSRmd4TXpVMVVGcFVVbFZFTFZKTGJuRlNPWEJGUVhkcVVtMHljVGgzTnpCU1NXWlpNVlpDY0RCRk1sRmhZekJWZVZaYWJWQmxibVJzYUhwZk5rWjJjVE10VEZOSWJHOVhTakZ4TVdGSkxteHpTM1IyWVc1TlVUZEJXR05VYjFWZldXVTBObEU9IiwiYSI6eyJmbmlkIjoiMDAwMDEzIiwiZnRpZCI6InR0bnYyIiwiZmNpZCI6InR0bi12Mi1ldS00In19",
                    }
                ],
                "settings": {
                    "data_rate": {
                        "lora": {"bandwidth": 125000, "spreading_factor": 12}
                    },
                    "coding_rate": "4/5",
                    "frequency": "868100000",
                },
                "received_at": "2021-09-21T10:35:57.125514417Z",
                "consumed_airtime": "1.482752s",
                "version_ids": {
                    "brand_id": "elsys",
                    "model_id": "ers-lite",
                    "hardware_version": "1.0",
                    "firmware_version": "1.0",
                    "band_id": "EU_863_870",
                },
                "network_ids": {
                    "net_id": "000013",
                    "tenant_id": "ttn",
                    "cluster_id": "ttn-eu1",
                },
            },
        }

        rx_message = v3_handler._extract_rx_message(message_without_rate)

        assert rx_message.device_eui == bytearray.fromhex("A81758FFFE053C84")
        assert rx_message.device_id == "66b8ccaa-90b9-2d24-bf59-0ea9e23b3bb4"
        assert rx_message.raw_data == base64.b64decode("BgLHBgKrBgL6")
        assert rx_message.rx_datetime == dtparser.parse(
            "2021-09-21T10:35:57.125514417Z"
        )
        assert rx_message.rx_port == 5

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
