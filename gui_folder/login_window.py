import tkinter as tk
from tkinter import ttk, messagebox
from gui_folder.chat_window import ChatWindow
from channel.channelManager import ChannelManager
from user.user import User


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Connexion au Chat")
        self.geometry("300x200")
        self.resizable(False, False)

        self.pseudo = tk.StringVar()
        self.salon = tk.StringVar(value="general")

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Pseudo").pack(pady=5)
        tk.Entry(self, textvariable=self.pseudo).pack(pady=5)

        tk.Label(self, text="Salon").pack(pady=5)
        salons = ["general", "tech", "random"]
        ttk.Combobox(self, textvariable=self.salon, values=salons, state="readonly").pack(pady=5)

        tk.Button(self, text="Se connecter", command=self.on_connect).pack(pady=20)

    def on_connect(self):
        pseudo = self.pseudo.get().strip()
        salon = self.salon.get().strip()

        if not pseudo:
            messagebox.showerror("Erreur", "Veuillez entrer un pseudo.")
            return

        self.manager = ChannelManager()
        self.user = User(pseudo=pseudo)  # On passe le pseudo GUI ici

        # 1) s'abonner aux salons publics initiaux
        self.manager.create_channel(salon)
        self.manager.subscribe_all(None)

        # 2) créer & s'abonner à son canal personnel
        my_id = User.generate_user_id(pseudo)
        self.manager.create_channel(my_id)
        personal_channel = self.manager.get_channel(my_id)
        personal_channel.set_on_message_callback(self.receive_dm_invitation)
        personal_channel.subscribe()

        # 3) s'abonner + publier sur "annuaire"
        self.manager.create_channel("annuaire")
        self.manager.get_channel("annuaire").subscribe()
        self.user.send_raw(my_id, "annuaire")

        self.destroy()
        ChatWindow(pseudo, salon, self.user, self.manager).mainloop()
       
    def receive_dm_invitation(self, message):
        # Exemple message: "DM_INVITE::chat_pierre_alex"
        if message.startswith("DM_INVITE::"):
            parts = message.split("::", 1)
            if len(parts) == 2 and parts[1].startswith("dm_") and len(parts[1]) > 6:
                salon = parts[1]
                if messagebox.askyesno("Invitation", f"Rejoindre le salon privé '{salon}' ?"):
                    self.manager.create_channel(salon)
                    self.manager.get_channel(salon).subscribe()
                    self.destroy()
                    ChatWindow(self.pseudo.get(), salon, self.user, self.manager).mainloop()
            else:
                print("[ERREUR] Format d'invitation DM invalide :", message)

            print(f"[INFO] Invitation reçue pour rejoindre le salon : {salon}")

            # Optionnel : boite de dialogue
            if messagebox.askyesno("Invitation", f"Rejoindre le salon privé '{salon}' ?"):
                self.manager.create_channel(salon)
                self.manager.get_channel(salon).subscribe()
                self.destroy()  # fermer fenêtre login
                ChatWindow(self.pseudo.get(), salon, self.user, self.manager).mainloop()
