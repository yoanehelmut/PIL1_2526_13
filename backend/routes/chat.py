from datetime import datetime, timezone

from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room

# Importation de l'instance socketio et de la base de données
# from extensions import socketio, db
# from models.message import Message


def init_chat_events(socketio):

    # -------------------------------------------------------------------------
    # Connexion / Déconnexion
    # -------------------------------------------------------------------------

    @socketio.on('connect')
    def handle_connect():
        if not current_user.is_authenticated:
            # Refuse la connexion si l'utilisateur n'est pas authentifié
            return False
        print(f"[CONNECT] Utilisateur {current_user.id} connecté (SID: {request.sid})")

    @socketio.on('disconnect')
    def handle_disconnect():
        user_id = current_user.id if current_user.is_authenticated else "inconnu"
        print(f"[DISCONNECT] Utilisateur {user_id} déconnecté (SID: {request.sid})")

    # -------------------------------------------------------------------------
    # Rejoindre une discussion privée
    # -------------------------------------------------------------------------

    @socketio.on('join_chat')
    def handle_join_chat(data):
        """
        Permet à un utilisateur authentifié de rejoindre la room privée
        partagée avec un contact.
        Reçoit : contact_id
        """
        if not current_user.is_authenticated:
            emit('error', {'message': 'Non authentifié'})
            return

        contact_id = data.get('contact_id')

        if not contact_id:
            emit('error', {'message': 'contact_id manquant'})
            return

        # On trie les IDs pour garantir un nom de room identique des deux côtés.
        room_name = _build_room_name(current_user.id, contact_id)
        join_room(room_name)
        print(f"[JOIN] Utilisateur {current_user.id} a rejoint la room : {room_name}")

    # -------------------------------------------------------------------------
    # Quitter une discussion privée
    # -------------------------------------------------------------------------

    @socketio.on('leave_chat')
    def handle_leave_chat(data):
        """
        Permet à un utilisateur de quitter proprement la room d'une discussion.
        Reçoit : contact_id
        """
        if not current_user.is_authenticated:
            emit('error', {'message': 'Non authentifié'})
            return

        contact_id = data.get('contact_id')

        if not contact_id:
            emit('error', {'message': 'contact_id manquant'})
            return

        room_name = _build_room_name(current_user.id, contact_id)
        leave_room(room_name)
        print(f"[LEAVE] Utilisateur {current_user.id} a quitté la room : {room_name}")

    # -------------------------------------------------------------------------
    # Envoi d'un message
    # -------------------------------------------------------------------------

    @socketio.on('send_message')
    def handle_send_message(data):
        """
        Gère l'envoi d'un message en temps réel.
        Reçoit : receiver_id, content
        L'expéditeur est déterminé côté serveur via current_user (sécurité).
        """
        if not current_user.is_authenticated:
            emit('error', {'message': 'Non authentifié'})
            return

        receiver_id = data.get('receiver_id')
        content = data.get('content', '').strip()

        if not receiver_id or not content:
            emit('error', {'message': 'receiver_id et content sont obligatoires'})
            return

        sender_id = current_user.id  # Source fiable : jamais le client
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Sauvegarde du message en base de données
        try:
            pass  # Décommenter ci-dessous pour activer la persistance :
            # new_msg = Message(
            #     sender_id=sender_id,
            #     receiver_id=receiver_id,
            #     content=content,
            #     timestamp=timestamp,
            # )
            # db.session.add(new_msg)
            # db.session.commit()
        except Exception as e:
            print(f"[ERROR] Sauvegarde BDD : {e}")
            emit('error', {'message': 'Erreur lors de la sauvegarde du message'})
            return

        # 2. Diffusion du message dans la room concernée
        room_name = _build_room_name(sender_id, receiver_id)

        message_payload = {
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'content': content,
            'timestamp': timestamp,   # ISO 8601 UTC — exploitable directement côté client
        }

        emit('receive_message', message_payload, to=room_name)
        print(f"[MSG] {sender_id} → {receiver_id} dans {room_name} : {content[:50]}")


# -----------------------------------------------------------------------------
# Utilitaire
# -----------------------------------------------------------------------------

def _build_room_name(user_id_a, user_id_b) -> str:
    """Construit un nom de room déterministe et symétrique pour deux utilisateurs."""
    return f"room_{min(user_id_a, user_id_b)}_{max(user_id_a, user_id_b)}"