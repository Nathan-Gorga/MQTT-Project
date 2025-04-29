from channel.channelManager import ChannelManager
from user.user import User

if __name__ == "__main__":
    manager = ChannelManager()
    user = User()

    # Crée des channels
    manager.create_channel("general")
    manager.create_channel("tech")
    manager.create_channel("random")

    # Abonne à tous les channels avec callback
    def on_message(channel_name, msg):
        print(f"[reçu sur {channel_name}] {msg}")

    manager.subscribe_all(on_message)

    try:
        while True:
            print("\nCanaux disponibles :", manager.list_channels())
            selected = input("Dans quel canal voulez-vous écrire ? (ou 'exit') : ")
            if selected.lower() == "exit":
                break
            if selected not in manager.list_channels():
                print("❌ Canal inconnu.")
                continue
            message = input("Message : ")
            user.send_message(message, selected)
    finally:
        manager.stop_all()
