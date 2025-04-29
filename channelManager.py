from channel.channel import Channel
from utils.utils import getBrokerAddress, getBrokerPort


class ChannelManager:
    def __init__(self, broker_address=getBrokerAddress(), port=getBrokerPort()):
        self.channels = {}
        self.broker_address = broker_address
        self.port = port

    def create_channel(self, name):
        if name not in self.channels:
            channel = Channel(name, self.broker_address, self.port)
            self.channels[name] = channel
            return channel
        return self.channels[name]

    def list_channels(self):
        return list(self.channels.keys())

    def get_channel(self, name):
        return self.channels.get(name)

    def subscribe_all(self, on_message_callback):
        for channel in self.channels.values():
            channel.set_on_message_callback(on_message_callback)
            channel.subscribe()

    def stop_all(self):
        for channel in self.channels.values():
            channel.stop()

