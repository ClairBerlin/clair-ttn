from clairttn.types import *

class ClairchenDeviceUUID(DeviceUUID):
    def __init__(self, device_id: bytes):
        super().__init__(device_id, "CLAIRCHEN")
