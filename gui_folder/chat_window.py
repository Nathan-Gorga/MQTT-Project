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
        # === Layout général : Sidebar + Chat ===
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        # === Sidebar gauche ===
        sidebar = tk.Frame(main_frame, width=150, bg="#eaeaea")
        sidebar.pack(side="left", fill="y")

        tk.Label(sidebar, text="Salons", bg="#eaeaea", font=("Arial", 10, "bold")).pack(pady=(10, 5))

        self.salons_disponibles = ["general", "tech", "random"]
        for salon in self.salons_disponibles:
            btn = tk.Button(sidebar, text=salon, anchor="w", command=lambda s=salon: self.select_channel(s))
            btn.pack(fill="x", padx=10, pady=2)

        # === Zone chat à droite ===
        chat_frame = tk.Frame(main_frame)
        chat_frame.pack(side="right", fill="both", expand=True)

        # Top (pseudo)
        top_frame = tk.Frame(chat_frame)
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(top_frame, text="Pseudo :").pack(side="left")
        self.pseudo_var = tk.StringVar(value=self.pseudo)
        tk.Entry(top_frame, textvariable=self.pseudo_var, width=20).pack(side="left", padx=(5, 10))
        tk.Button(top_frame, text="Changer", command=self.change_pseudo).pack(side="left")

        # Salon actif affiché
        self.salon_var_label = tk.Label(chat_frame, text=f"Salon actuel : {self.salon}", fg="gray")
        self.salon_var_label.pack(anchor="w", padx=10)

        # Zone messages
        self.chat_area = tk.Text(chat_frame, state="disabled", wrap="word", bg="#f9f9f9", height=15)
        self.chat_area.pack(fill="both", expand=True, padx=10)

        # Entrée + bouton envoyer
        bottom_frame = tk.Frame(chat_frame)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.message = tk.StringVar()
        self.entry = tk.Entry(bottom_frame, textvariable=self.message)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.send_message())

        tk.Button(bottom_frame, text="Envoyer", command=self.send_message).pack(side="right", padx=(10, 0))





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

    def select_channel(self, nouveau_salon):
        if nouveau_salon == self.salon:
            return

        # Désabonnement de l'ancien salon
        ancien_channel = self.manager.get_channel(self.salon)
        if ancien_channel:
            ancien_channel.unsubscribe()

        self.salon = nouveau_salon
        self.salon_var_label.config(text=f"Salon actuel : {self.salon}")

        # Créer ou récupérer et rebind le callback
        self.manager.create_channel(nouveau_salon)
        channel = self.manager.get_channel(nouveau_salon)
        channel.set_on_message_callback(self.receive_message)
        channel.subscribe()

        self.display_message("Système", f"Salon changé pour : {self.salon}")

