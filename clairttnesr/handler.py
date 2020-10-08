import ttn
import logging

def process_uplink_message(message, client):
    logging.debug("uplink message received from {}".format(message.dev_id))
    logging.debug(str(message))

class Handler:
    def __init__(self, app_id, access_key):
        logging.debug("app id: {}".format(app_id))
        ttnHandler = ttn.HandlerClient(app_id, access_key)
        self._mqtt_client = ttnHandler.data()
        self._mqtt_client.set_uplink_callback(process_uplink_message)

    def connect(self):
        self._mqtt_client.connect()

    def close(self):
        self._mqtt_client.close()
