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

        self.manager.create_channel(salon)
        self.manager.subscribe_all(None)  # Callback branché plus tard dans ChatWindow

        self.destroy()
        ChatWindow(pseudo, salon, self.user, self.manager).mainloop()