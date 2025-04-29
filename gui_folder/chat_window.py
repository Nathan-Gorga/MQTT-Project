import tkinter as tk
from tkinter import ttk

class ChatWindow(tk.Tk):
    def __init__(self, pseudo, salon, user, manager):
        super().__init__()
        self.title(f"Salon : {salon}")
        self.geometry("500x400")
        self.resizable(True, True)

        self.pseudo = pseudo
        self.salon = salon
        self.user = user
        self.manager = manager

        self.salon_var = tk.StringVar(value=salon)
        self.create_widgets()

        # Brancher la réception des messages
        channel = self.manager.get_channel(salon)
        if channel:
            channel.set_on_message_callback(self.receive_message)

    def create_widgets(self):
        self.chat_area = tk.Text(self, state="disabled", wrap="word", bg="#f2f2f2")
        self.chat_area.pack(padx=10, pady=10, expand=True, fill="both")

        frame = tk.Frame(self)
        frame.pack(fill="x", padx=10, pady=5)

        self.message = tk.StringVar()
        entry = tk.Entry(frame, textvariable=self.message)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.send_message())

        tk.Button(frame, text="Envoyer", command=self.send_message).pack(side="right")

        salons = ["general", "tech", "random"]
        self.salon_menu = ttk.Combobox(self, textvariable=self.salon_var, values=salons, state="readonly")
        self.salon_menu.pack(pady=5)
        self.salon_menu.bind("<<ComboboxSelected>>", self.on_change_salon)

    def display_message(self, author, text):
        self.chat_area.config(state="normal")
        self.chat_area.insert("end", f"{author} : {text}\n")
        self.chat_area.see("end")
        self.chat_area.config(state="disabled")

    def receive_message(self, channel_name, msg):
        if msg:
            auteur, _, contenu = msg.partition(": ")
            self.display_message(auteur.strip(), contenu.strip())

    def send_message(self):
        msg = self.message.get().strip()
        if msg:
            self.message.set("")
            self.user.send_message(msg, self.salon)  # Publie via MQTT

    def on_change_salon(self, event):
        nouveau_salon = self.salon_var.get()
        if nouveau_salon == self.salon:
            return

        # Désabonnement ancien salon
        ancien_channel = self.manager.get_channel(self.salon)
        if ancien_channel:
            ancien_channel.unsubscribe()

        # Création et abonnement nouveau salon
        self.salon = nouveau_salon
        self.manager.create_channel(nouveau_salon)
        new_channel = self.manager.get_channel(nouveau_salon)
        new_channel.set_on_message_callback(self.receive_message)
        new_channel.subscribe()

        self.title(f"Salon : {self.salon}")
        self.display_message("Système", f"Salon changé pour : {self.salon}")