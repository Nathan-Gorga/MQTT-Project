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

        self.manager.create_channel(self.user.user_id)
        personal_channel = self.manager.get_channel(self.user.user_id)
        personal_channel.set_on_message_callback(self.on_personal_message)
        personal_channel.subscribe()
        # Mon identifiant DM
        self.my_id = self.user.user_id

        # Écoute des invitations : sur mon canal perso
        self.manager.get_channel(self.my_id).set_on_message_callback(self.receive_dm_invitation)

        # (Optionnel) écoute de l'annuaire pour afficher la liste d’utilisateurs
        self.known_users = set()
        self.manager.get_channel("annuaire").set_on_message_callback(self.receive_annuaire_entry)


        self.salon_widgets = {}  # ✅ Initialisé ici pour éviter l'erreur


        self.salon_var = tk.StringVar(value=salon)
        
        
        self.local_storage = {}  # Stocke tous les messages de chaque salon


        self.salons_disponibles = ["general", "tech", "random"]
        

        # s'abonne une fois via l'objet user
        self.user.subscribe_to_channels(self.salons_disponibles, self.receive_message)

        self.create_widgets()


    def on_message_received(self, topic, message):
        print(f"[MQTT] Message reçu sur {topic}: {message}")

        # Affichage direct si c’est le canal actif
        if topic == self.current_channel:
            self.display_message(message)
        else:
            self.notify_new_message(topic)
            
    def on_personal_message(self, topic, msg):
        try:
            if msg.startswith("dm_"):  # Une invitation à un DM
                self.receive_dm_invitation(topic, msg)
            else:
                self.on_message_received(topic, msg)
        except Exception as e:
            print("Erreur dans le callback perso :", e)

    def create_widgets(self):
        
        
        

        # === Layout général : Sidebar + Chat ===
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        # === Sidebar gauche stylée ===
        sidebar = tk.Frame(main_frame, width=200, bg="#f0f0f0", bd=1, relief="solid")
        sidebar.pack(side="left", fill="y")

        tk.Label(sidebar, text="Salons", bg="#f0f0f0", font=("Arial", 11, "bold")).pack(pady=(10, 5))

        self.salons_disponibles = ["general", "tech", "random"]
        for salon in self.salons_disponibles:
            bloc = tk.Frame(sidebar, bg="#ffffff", bd=1, relief="groove", padx=5, pady=5)
            bloc.pack(fill="x", pady=2, padx=5)

            salon_label = tk.Label(bloc, text=salon, font=("Arial", 10, "bold"), anchor="w", bg="#ffffff")
            salon_label.pack(fill="x")

            last_msg = tk.Label(bloc, text="", font=("Arial", 8), fg="gray", anchor="w", bg="#ffffff")
            last_msg.pack(fill="x")

            bloc.bind("<Button-1>", lambda e, s=salon: self.select_channel(s))
            salon_label.bind("<Button-1>", lambda e, s=salon: self.select_channel(s))
            last_msg.bind("<Button-1>", lambda e, s=salon: self.select_channel(s))

            self.salon_widgets[salon] = {"frame": bloc, "label": salon_label, "last_msg": last_msg}


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

        tk.Button(bottom_frame, text="Image", command=self.send_image).pack(side="right", padx=(0, 5))
        
        salon_create_frame = tk.Frame(self)
        salon_create_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.new_channel_var = tk.StringVar()
        tk.Button(salon_create_frame, text="Créer salon", command=self.show_create_channel_popup).pack(side="left", padx=(5, 0))
        
        # Bouton DM
        # salon_create_frame = tk.Frame(self)
        # salon_create_frame.pack(fill="x", padx=10, pady=(0, 10))
        # tk.Button(salon_create_frame, text="DM", command=self.show_dm_popup).pack(side="left", padx=(5, 0))



    def display_message(self, sender, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert('end', f"{sender}: {message}\n")
        self.chat_area.config(state='disabled')
        self.chat_area.see('end')
      
    def receive_message(self, channel_name, msg):
        try:
            # 👉 Cas image JSON
            payload = json.loads(msg)
            if isinstance(payload, dict) and payload.get("type") == "image":
                author = payload.get("author", "Inconnu")
                image_data = payload.get("data")
                self.store_local_message(channel_name, author, payload)
                if self.salon == channel_name:
                    self.display_image(author, image_data)
                return  # stop ici si image traitée
        except Exception:
            pass  # Pas un JSON valide : on traite comme texte brut

        auteur, _, contenu = msg.partition(": ")
        self.store_local_message(channel_name, auteur.strip(), contenu.strip())


        # Affichage si on est dans le bon salon
        if channel_name == self.salon:
            self.display_message(auteur.strip(), contenu.strip())

        # Aperçu dans la sidebar
        if channel_name in self.salon_widgets:
            preview = contenu[:10] + "..." if len(contenu) > 10 else contenu
            self.salon_widgets[channel_name]["last_msg"].config(text=preview)
    
    
    
    
    def receive_dm_invitation(self, channel_name, msg):
        """Reçoit une invitation DM sur mon canal personnel."""
        dm_channel_name = msg.strip()

        if not dm_channel_name:
            self.display_message("Système", "Invitation DM invalide (nom de canal vide).")
            return

        if dm_channel_name in self.salons_disponibles:
            self.display_message("Système", f"Le salon '{dm_channel_name}' est déjà présent.")
            return

        # Abonnement au nouveau canal
        self.manager.create_channel(dm_channel_name)
        channel = self.manager.get_channel(dm_channel_name)
        channel.set_on_message_callback(self.receive_message)
        
        channel.subscribe()

        # Ajout dans la liste de salons
        self.salons_disponibles.append(dm_channel_name)

        # Création de l'interface dans la sidebar
        sidebar_frame = list(self.children.values())[0].winfo_children()[0]  # frame de gauche

        bloc = tk.Frame(sidebar_frame, bg="#ffffff", bd=1, relief="groove", padx=5, pady=5)
        bloc.pack(fill="x", pady=2, padx=5)

        salon_label = tk.Label(bloc, text=dm_channel_name, font=("Arial", 10, "bold"), anchor="w", bg="#ffffff")
        salon_label.pack(fill="x")

        last_msg = tk.Label(bloc, text="", font=("Arial", 8), fg="gray", anchor="w", bg="#ffffff")
        last_msg.pack(fill="x")

        bloc.bind("<Button-1>", lambda e, s=dm_channel_name: self.select_channel(s))
        salon_label.bind("<Button-1>", lambda e, s=dm_channel_name: self.select_channel(s))
        last_msg.bind("<Button-1>", lambda e, s=dm_channel_name: self.select_channel(s))

        self.salon_widgets[dm_channel_name] = {
            "frame": bloc,
            "label": salon_label,
            "last_msg": last_msg
        }

        self.display_message("Système", f"Invitation DM reçue. Connecté au salon '{dm_channel_name}'.")

        # Optionnel : basculer automatiquement vers le DM
        self.select_channel(dm_channel_name)

    def receive_annuaire_entry(self, channel_name, msg):
        """Nouvel identifiant publié sur 'annuaire'."""
        if msg not in self.known_users:
            self.known_users.add(msg)
            print(f"[Annuaire] nouvel utilisateur : {msg}")

    def show_dm_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Nouvelle DM")
        popup.geometry("300x100")
        popup.grab_set()
        tk.Label(popup, text="ID destinataire :").pack(pady=(10,5))
        entry = tk.Entry(popup)
        entry.pack(pady=(0,5)); entry.focus()
        def send_invite():
            target = entry.get().strip()
            if not target:
                tk.messagebox.showerror("Erreur", "ID invalide")
                return
            # Génère canal DM aléatoire
            import random, string
            chan = "dm_" + ''.join(random.choices(string.ascii_letters+string.digits, k=6))
            # Crée, souscrit, sélectionne
            self.manager.create_channel(chan)
            dm = self.manager.get_channel(chan)
            dm.set_on_message_callback(self.receive_message)
            dm.subscribe()
            self.salons_disponibles.append(chan)
            self.select_channel(chan)
            # Envoie invitation sur le canal perso de target
            self.user.send_raw(target, f"DM_INVITE::{chan}")
            print(f"connect to DM_INVITE::{chan}")
            self.display_message("Système", f"Invitation DM envoyée à {target}")
            popup.destroy()
            sidebar_frame = list(self.children.values())[0].winfo_children()[0]  # récupère la frame de gauche

            bloc = tk.Frame(sidebar_frame, bg="#ffffff", bd=1, relief="groove", padx=5, pady=5)
            bloc.pack(fill="x", pady=2, padx=5)

            salon_label = tk.Label(bloc, text=target, font=("Arial", 10, "bold"), anchor="w", bg="#ffffff")
            salon_label.pack(fill="x")

            last_msg = tk.Label(bloc, text="", font=("Arial", 8), fg="gray", anchor="w", bg="#ffffff")
            last_msg.pack(fill="x")

            bloc.bind("<Button-1>", lambda e, s=chan: self.select_channel(s))
            salon_label.bind("<Button-1>", lambda e, s=chan: self.select_channel(s))
            last_msg.bind("<Button-1>", lambda e, s=chan: self.select_channel(s))

            self.salon_widgets[chan] = {
                "frame": bloc,
                "label": salon_label,
                "last_msg": last_msg
            }
        tk.Button(popup, text="Envoyer", command=send_invite).pack()
        



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

    def select_channel(self, nouveau_salon):
        if nouveau_salon == self.salon:
            return

        # Désabonnement de l'ancien salon
        ancien_channel = self.manager.get_channel(self.salon)
        if ancien_channel:
            ancien_channel.unsubscribe()

        self.salon = nouveau_salon
        self.salon_var_label.config(text=f"Salon actuel : {self.salon}")

        self.display_message("Système", f"Salon changé pour : {self.salon}")

        # Réabonnement MQTT au nouveau salon
        self.manager.create_channel(nouveau_salon)
        new_channel = self.manager.get_channel(nouveau_salon)
        new_channel.set_on_message_callback(self.receive_message)
       # new_channel.subscribe()

        # Vider et réafficher l'historique du nouveau salon
        self.chat_area.config(state="normal")
        self.chat_area.delete("1.0", "end")
        self.chat_area.config(state="disabled")
        self.display_local_history(self.salon)

            
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

        if new_channel in self.salons_disponibles:
            self.display_message("Système", f"Le salon '{new_channel}' existe déjà.")
            return

        # Ajouter au modèle
        self.salons_disponibles.append(new_channel)

        # Abonnement MQTT
        self.user.subscribe_to_channels([new_channel], self.receive_message)

        # Création UI bloc dans la sidebar
        sidebar_frame = list(self.children.values())[0].winfo_children()[0]  # récupère la frame de gauche

        bloc = tk.Frame(sidebar_frame, bg="#ffffff", bd=1, relief="groove", padx=5, pady=5)
        bloc.pack(fill="x", pady=2, padx=5)

        salon_label = tk.Label(bloc, text=new_channel, font=("Arial", 10, "bold"), anchor="w", bg="#ffffff")
        salon_label.pack(fill="x")

        last_msg = tk.Label(bloc, text="", font=("Arial", 8), fg="gray", anchor="w", bg="#ffffff")
        last_msg.pack(fill="x")

        bloc.bind("<Button-1>", lambda e, s=new_channel: self.select_channel(s))
        salon_label.bind("<Button-1>", lambda e, s=new_channel: self.select_channel(s))
        last_msg.bind("<Button-1>", lambda e, s=new_channel: self.select_channel(s))

        self.salon_widgets[new_channel] = {
            "frame": bloc,
            "label": salon_label,
            "last_msg": last_msg
        }

        self.display_message("Système", f"Salon '{new_channel}' créé.")
        self.select_channel(new_channel)


       
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
    
    
    def send_dm_invitation(self, recipient_pseudo):
        salon_name = f"dm_{self.pseudo}_{recipient_pseudo}"

        # Crée le salon en local
        self.manager.create_channel(salon_name)
        self.manager.get_channel(salon_name).subscribe()

        # Récupère l'user_id complet du destinataire
        from user.user import User  # en haut du fichier s'il manque

        target_id = User.generate_user_id(recipient_pseudo)
        self.user.send_raw(f"DM_INVITE::{salon_name}", target_id)

        # Ouvre direct le salon chez l’émetteur
        ChatWindow(self.pseudo, salon_name, self.user, self.manager).mainloop()
        

