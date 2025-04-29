# === gui/chat_window.py ===
import tkinter as tk
from tkinter import ttk

class ChatWindow(tk.Tk):
    def __init__(self, pseudo, salon):
        super().__init__()
        self.title(f"Salon : {salon}")
        self.geometry("500x400")
        self.resizable(True, True)

        self.pseudo = pseudo
        self.salon = salon
        self.salon_var = tk.StringVar(value=salon)

        self.create_widgets()

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

        salons = ["général", "dev", "random"]
        self.salon_menu = ttk.Combobox(self, textvariable=self.salon_var, values=salons, state="readonly")
        self.salon_menu.pack(pady=5)
        self.salon_menu.bind("<<ComboboxSelected>>", self.on_change_salon)

    def display_message(self, author, text):
        self.chat_area.config(state="normal")
        self.chat_area.insert("end", f"{author} : {text}\n")
        self.chat_area.see("end")
        self.chat_area.config(state="disabled")

    def send_message(self):
        msg = self.message.get().strip()
        if msg:
            self.display_message(self.pseudo, msg)
            self.message.set("")
            # Intégration MQTT plus tard

    def on_change_salon(self, event):
        nouveau_salon = self.salon_var.get()
        self.salon = nouveau_salon
        self.title(f"Salon : {self.salon}")
        self.display_message("Système", f"Salon changé pour : {self.salon}")
        # self.mqtt.change_salon(nouveau_salon) plus tard

