import paho.mqtt.client as mqtt
from utils.utils import getBrokerAddress, getBrokerPort

class Channel:
    def __init__(self, name, broker_address=getBrokerAddress(), port=getBrokerPort()):
        self.name = name
        self.broker_address = broker_address
        self.port = port
        self.client = mqtt.Client()
        self.client.on_message = self._internal_on_message
        self.on_message_callback = None
        self.connected = False  # pour éviter plusieurs loop_start()

    def connect(self):
        if not self.connected:
            self.client.connect(self.broker_address, self.port)
            self.client.loop_start()
            self.connected = True

    def subscribe(self):
        self.connect()
        self.client.subscribe(self.name)

    def unsubscribe(self):
        self.client.unsubscribe(self.name)

    def _internal_on_message(self, client, userdata, message):
        content = message.payload.decode("utf-8")
        if self.on_message_callback:
            self.on_message_callback(self.name, content)
        else:
            print(f"[{self.name}] {content}")

    def set_on_message_callback(self, callback):
        self.on_message_callback = callback

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        print(f"Déconnecté du canal '{self.name}'")
        self.connected = False
