# from clairttners.handler import ERS_PARAMETER_SETS, _encode_parameter_set
# from clairserver.ingestair.ttn.lorawandefinitions import LoRaWanMcs
# 
# # generated using the ELSYS Downlink Generator
# # https://www.elsys.se/en/downlink-generator/
# # according to
# # https://docs.google.com/spreadsheets/d/1oWVQ4jNrC2VMZ8UkpnLZMsMh9QyX5it7FH3Bk12c-1E/edit#gid=0
# EXPECTED_ENCODINGS = {
#     LoRaWanMcs.SF12BW125: bytes.fromhex('3E0F14000003B415000000001F00000005'),
#     LoRaWanMcs.SF11BW125: bytes.fromhex('3E0F140000025115000000001F00000004'),
#     LoRaWanMcs.SF10BW125: bytes.fromhex('3E0F140000016415000000001F00000003'),
#     LoRaWanMcs.SF9BW125: bytes.fromhex('3E0F140000014615000000011F00000002'),
#     LoRaWanMcs.SF8BW125: bytes.fromhex('3E0F140000014615000000011F00000002'),
#     LoRaWanMcs.SF7BW125: bytes.fromhex('3E0F140000014615000000011F00000002'),
#     LoRaWanMcs.SF7BW250: bytes.fromhex('3E0F140000014615000000011F00000002')
# }
# 
# def test_parameter_set_encodings():
#     for mcs in LoRaWanMcs:
#         parameter_set = ERS_PARAMETER_SETS[mcs]
#         assert(_encode_parameter_set(parameter_set) == EXPECTED_ENCODINGS[mcs])
