import tkinter as tk
from tkinter import ttk
import base64
import json
from tkinter import filedialog
from PIL import Image, ImageTk
import io


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
        self.local_storage = {}

        # Brancher la réception des messages
        channel = self.manager.get_channel(salon)
        if channel:
            channel.set_on_message_callback(self.receive_message)

    def create_widgets(self):
        # === Zone top : Pseudo + changement ===
        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(top_frame, text="Pseudo :").pack(side="left")
        self.pseudo_var = tk.StringVar(value=self.pseudo)
        tk.Entry(top_frame, textvariable=self.pseudo_var, width=20).pack(side="left", padx=(5, 10))
        tk.Button(top_frame, text="Changer", command=self.change_pseudo).pack(side="left")

        # === Menu déroulant des salons ===
        self.salon_menu = ttk.Combobox(self, textvariable=self.salon_var,
                                        values=["general", "tech", "random"],
                                        state="readonly")
        self.salon_menu.pack(fill="x", padx=10, pady=(0, 10))
        self.salon_menu.bind("<<ComboboxSelected>>", self.on_change_salon)

        # === Zone d'affichage des messages ===
        self.chat_area = tk.Text(self, state="disabled", wrap="word", bg="#f9f9f9", height=15)
        self.chat_area.pack(fill="both", expand=True, padx=10)

        # === Zone d’écriture + bouton envoyer ===
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.message = tk.StringVar()
        self.entry = tk.Entry(bottom_frame, textvariable=self.message)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.send_message())

        tk.Button(bottom_frame, text="Envoyer", command=self.send_message).pack(side="right", padx=(10, 0))

        tk.Button(bottom_frame, text="Image", command=self.send_image).pack(side="right", padx=(0, 5))
        
        salon_create_frame = tk.Frame(self)
        salon_create_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.new_channel_var = tk.StringVar()
        tk.Button(salon_create_frame, text="Créer salon", command=self.show_create_channel_popup).pack(side="left", padx=(5, 0))


    def display_message(self, author, text):
        self.chat_area.config(state="normal")
        self.chat_area.insert("end", f"{author} : {text}\n")
        self.chat_area.see("end")
        self.chat_area.config(state="disabled")

    def receive_message(self, channel_name, msg):
        try:
            payload = json.loads(msg)
            if isinstance(payload, dict) and payload.get("type") == "image":
                author = payload.get("author", "Inconnu")
                image_data = payload.get("data")
                self.store_local_message(channel_name, author, payload)
                if self.salon == channel_name:
                    self.display_image(author, image_data)
                return
        except Exception:
            pass  # Si erreur ou pas un JSON, on considère un message texte

        auteur, _, contenu = msg.partition(": ")
        self.store_local_message(channel_name, auteur.strip(), contenu.strip())
        if self.salon == channel_name:
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

        # Mise à jour salon courant
        self.salon = nouveau_salon
        self.title(f"Salon : {self.salon}")

        # Abonnement au nouveau
        self.manager.create_channel(nouveau_salon)
        new_channel = self.manager.get_channel(nouveau_salon)
        new_channel.set_on_message_callback(self.receive_message)
        new_channel.subscribe()

        # Nettoyer la zone et afficher l’historique
        self.chat_area.config(state="normal")
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.config(state="disabled")

        self.display_message("Système", f"Salon changé pour : {self.salon}")
        self.display_local_history(self.salon)


    def change_pseudo(self):
        new_pseudo = self.pseudo_var.get().strip()
        if new_pseudo:
            self.pseudo = new_pseudo
            self.user.pseudo = new_pseudo
            self.display_message("Système", f"Pseudo changé pour : {self.pseudo}")
            
    def store_local_message(self, channel, author, content):
        if channel not in self.local_storage:
            self.local_storage[channel] = []
        self.local_storage[channel].append((author, content))
        
    def display_local_history(self, salon):
        messages = self.local_storage.get(salon, [])
        for author, content in messages:
            if isinstance(content, dict) and content.get("type") == "image":
                self.display_image(author, content.get("data"))
            else:
                self.display_message(author, content)

   

    def send_image(self):
        filepath = filedialog.askopenfilename(
            title="Choisir une image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif")]
        )
        if not filepath:
            return

        # Lecture + encodage
        with open(filepath, "rb") as f:
            image_bytes = f.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Construction du JSON
        payload = {
            "type": "image",
            "author": self.pseudo,
            "data": image_b64
        }
        json_payload = json.dumps(payload)

        # Publication **sans** préfixe
        # on utilise directement le client MQTT, sans passer par user.send_message
        self.user.client.publish(self.salon, json_payload)
        print(f"[envoyé image sur {self.salon}] {json_payload[:50]}…")
        
    def display_image(self, author, base64_data):
        import io
        from PIL import Image, ImageTk
        import base64

        image_data = base64.b64decode(base64_data)
        image = Image.open(io.BytesIO(image_data))
        image.thumbnail((200, 200))  # Tu peux ajuster la taille ici

        image_tk = ImageTk.PhotoImage(image)

        # Important : garder une référence sinon l'image disparaît
        if not hasattr(self, "images_refs"):
            self.images_refs = []
        self.images_refs.append(image_tk)

        self.chat_area.config(state="normal")
        self.chat_area.insert("end", f"{author} a envoyé une image :\n")
        self.chat_area.image_create("end", image=image_tk)
        self.chat_area.insert("end", "\n")
        self.chat_area.config(state="disabled")
        self.chat_area.see("end")
        
    def create_channel(self, new_channel):
        new_channel = new_channel.strip()
        if not new_channel:
            self.display_message("Système", "Nom de salon invalide.")
            return

        existing_channels = list(self.salon_menu["values"])
        if new_channel in existing_channels:
            self.display_message("Système", f"Le salon '{new_channel}' existe déjà.")
            return

        updated_channels = existing_channels + [new_channel]
        self.salon_menu["values"] = updated_channels
        self.salon_var.set(new_channel)
        self.on_change_salon(None)
        self.display_message("Système", f"Salon '{new_channel}' créé.")

       
    def show_create_channel_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Nouveau salon")
        popup.geometry("300x100")
        popup.grab_set()  # Rendre la fenêtre modale

        tk.Label(popup, text="Nom du salon :").pack(pady=(10, 5))
        entry_var = tk.StringVar()
        entry = tk.Entry(popup, textvariable=entry_var)
        entry.pack(pady=(0, 5))
        entry.focus()

        def validate():
            name = entry_var.get().strip()
            if name:
                self.create_channel(name)
                popup.destroy()
            else:
                tk.messagebox.showerror("Erreur", "Le nom du salon ne peut pas être vide.")

        tk.Button(popup, text="Créer", command=validate).pack()
