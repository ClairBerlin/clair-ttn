from clairttn.types import *
import datetime as dt
from typing import List


class ClairchenDeviceUUID(DeviceUUID):
    """UUID for Clairchen devices"""

    def __init__(self, device_id: bytes):
        super().__init__(device_id, "CLAIRCHEN")


def decode_payload(payload: bytes, rx_datetime: dt.datetime, mcs: LoRaWanMcs) -> List[Sample]:
    return []
