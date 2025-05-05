import random
import string
import datetime
import hashlib
import paho.mqtt.client as mqtt
from utils.utils import getBrokerAddress, getBrokerPort

def createUserId():
    randomstring = ''.join(random.choice(string.ascii_letters) for _ in range(15))
    timestamp = datetime.datetime.now().isoformat()
    to_hash = f"{timestamp}{randomstring}".encode('utf-8')
    return hashlib.sha1(to_hash).hexdigest()

def createUserPseudo():
    return input("Veuillez renseigner votre pseudo : ")

class User:
    def __init__(self, pseudo, broker_address=getBrokerAddress(), port=getBrokerPort()):
        self.id = createUserId()
        self.pseudo = pseudo  # reçu depuis l'interface GUI
        self.client = mqtt.Client(client_id=self.id)
        self.client.connect(broker_address, port)
        self.client.loop_start()

    def send_message(self, message, channel_name):
        full_message = f"{self.pseudo} : {message}"
        self.client.publish(channel_name, full_message)
        print(f"[envoyé sur {channel_name}] {full_message}")

    def subscribe_to_channels(self, channels, callback):
        def on_message(client, userdata, message):
            channel = message.topic
            content = message.payload.decode("utf-8")
            callback(channel, content)

        self.client.on_message = on_message
        for ch in channels:
            self.client.subscribe(ch)
