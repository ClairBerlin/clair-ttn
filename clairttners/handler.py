import ttn
import logging
import base64
from clairserver.ingestair.ttn.elsys.ersprotocol_v0 import ElSysErsProtocol

def _process_uplink_message(message, client):
    logging.debug("uplink message received from {}".format(message.dev_id))
    logging.debug(str(message))
    pdu = base64.b64decode(message.payload_raw)
    logging.debug("decoded payload: {}".format(pdu))
    measurements = ElSysErsProtocol.decode_pdu(pdu)
    logging.debug("measurements: {}".format(measurements))

class Handler:
    def __init__(self, app_id, access_key):
        logging.debug("app id: {}".format(app_id))
        ttnHandler = ttn.HandlerClient(app_id, access_key)
        self._mqtt_client = ttnHandler.data()
        self._mqtt_client.set_uplink_callback(_process_uplink_message)

    def connect(self):
        self._mqtt_client.connect()

    def close(self):
        self._mqtt_client.close()
