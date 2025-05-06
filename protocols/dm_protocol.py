# dm_protocol.py

def make_dm_channel_name(user1_id, user2_id):
    """Retourne un nom canonique pour un canal DM entre deux utilisateurs"""
    sorted_users = sorted([user1_id, user2_id])
    return f"dm_{sorted_users[0]}_{sorted_users[1]}"


def is_dm_invitation(message):
    """Vérifie si le message est une invitation DM valide"""
    return message.startswith("DM_INVITE::")


def extract_dm_channel_name(message):
    """Extrait le nom du salon DM depuis une invitation"""
    if not is_dm_invitation(message):
        return None
    parts = message.split("::", 1)
    if len(parts) != 2:
        return None
    return parts[1] if parts[1].startswith("dm_") else None


def build_dm_invitation(channel_name):
    """Construit un message d'invitation DM"""
    return f"DM_INVITE::{channel_name}"


def should_ignore_dm(user_id, target_id):
    """Évite les auto-invitations"""
    return not target_id or user_id == target_id

# dm_protocol.py

def setup_personal_dm_channel(manager: ChannelManager, user: User, on_message_callback: Callable):
    """Crée le channel personnel et configure la réception d'invitations DM."""
    my_id = user.user_id
    manager.create_channel(my_id)
    personal_channel = manager.get_channel(my_id)
    personal_channel.set_on_message_callback(on_message_callback)
    personal_channel.subscribe()


def handle_dm_invitation(message: str, on_accept: Callable[[str], None]):
    """Traite un message d'invitation DM et appelle on_accept avec le nom du salon si accepté."""
    if not is_dm_invitation(message):
        return

    salon = extract_dm_channel_name(message)
    if not salon:
        return

    from tkinter import messagebox
    if messagebox.askyesno("Invitation", f"Rejoindre le salon privé '{salon}' ?"):
        on_accept(salon)
