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

        self.pseudo_var = tk.StringVar(value=pseudo)
        self.salon_var = tk.StringVar(value=salon)
        self.create_widgets()

        # Brancher la réception des messages
        channel = self.manager.get_channel(salon)
        if channel:
            channel.set_on_message_callback(self.receive_message)

    def create_widgets(self):
        # Zone d'affichage (lecture seule)
        self.chat_area = tk.Text(self, state="disabled", wrap="word", bg="#f9f9f9")
        self.chat_area.pack(padx=10, pady=(10, 0), expand=True, fill="both")

        # Scroll automatique
        self.chat_area_scrollbar = tk.Scrollbar(self.chat_area)
        self.chat_area.config(yscrollcommand=self.chat_area_scrollbar.set)
        self.chat_area_scrollbar.config(command=self.chat_area.yview)

        # Ligne de séparation
        separator = tk.Frame(self, height=2, bd=1, relief="sunken")
        separator.pack(fill="x", padx=5, pady=5)

        # Conteneur bas : champ + bouton
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.message = tk.StringVar()
        self.entry = tk.Entry(bottom_frame, textvariable=self.message)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.send_message())

        send_button = tk.Button(bottom_frame, text="Envoyer", command=self.send_message)
        send_button.pack(side="right", padx=(10, 0))

        # Menu déroulant pour changer de salon
        salons = ["general", "tech", "random"]
        self.salon_menu = ttk.Combobox(self, textvariable=self.salon_var, values=salons, state="readonly")
        self.salon_menu.pack(pady=(0, 5))
        self.salon_menu.bind("<<ComboboxSelected>>", self.on_change_salon)

        # Bloc de changement de pseudo
        pseudo_frame = tk.Frame(self)
        pseudo_frame.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(pseudo_frame, text="Pseudo :").pack(side="left")
        self.pseudo_var = tk.StringVar(value=self.pseudo)
        pseudo_entry = tk.Entry(pseudo_frame, textvariable=self.pseudo_var, width=20)
        pseudo_entry.pack(side="left", padx=(5, 10))

        tk.Button(pseudo_frame, text="Changer", command=self.change_pseudo).pack(side="left")



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

    def change_pseudo(self):
        new_pseudo = self.pseudo_var.get().strip()
        if new_pseudo:
            self.pseudo = new_pseudo
            self.user.pseudo = new_pseudo
            self.display_message("Système", f"Pseudo changé pour : {self.pseudo}")
