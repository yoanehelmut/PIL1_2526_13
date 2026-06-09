# =====================================================================
# Rôle : Gère l'historique de discussion et la passerelle WebSockets.
# =====================================================================

import pymysql
from datetime import datetime, timezone

from flask import request, session  # CORRIGÉ : Remplacement de Flask-Login par session
from flask_socketio import emit, join_room, leave_room

from config.database import get_db_connection  # CORRIGÉ : Ajout du connecteur BDD du groupe
from models.match import get_matching_by_users


def init_chat_events(socketio):

    @socketio.on('connect')
    def handle_connect():
        # CORRIGÉ : Vérification via la session globale de l'application
        if 'user_id' not in session:
            return False
        print(f"[CONNECT] Utilisateur {session['user_id']} connecté (SID: {request.sid})")

    @socketio.on('disconnect')
    def handle_disconnect():
        user_id = session.get('user_id', 'inconnu')  # CORRIGÉ : Session
        print(f"[DISCONNECT] Utilisateur {user_id} déconnecté (SID: {request.sid})")

    # -------------------------------------------------------------------------
    # Rejoindre une discussion privée
    # -------------------------------------------------------------------------

    @socketio.on('join_chat')
    def handle_join_chat(data):
        """
        Reçoit : conversation_id, contact_id
        Vérifie que les deux utilisateurs ont un matching accepté.
        """
        if 'user_id' not in session:  # CORRIGÉ : Session
            emit('error', {'message': 'Non authentifié'})
            return

        current_user_id = session['user_id']  # CORRIGÉ : Session
        conversation_id = data.get('conversation_id')
        contact_id = data.get('contact_id')

        if not conversation_id or not contact_id:
            emit('error', {'message': 'conversation_id et contact_id sont obligatoires'})
            return

        # Vérification d'autorisation via match.py
        # On teste les deux sens : current_user peut être étudiant OU mentor
        match = (
            get_matching_by_users(current_user_id, contact_id) or
            get_matching_by_users(contact_id, current_user_id)
        )

        if not match:
            emit('error', {'message': 'Accès refusé : aucun matching actif avec cet utilisateur'})
            print(f"[SECURITY] user:{current_user_id} a tenté de rejoindre conv:{conversation_id} sans matching valide")
            return

        room_name = _build_room_name(conversation_id)
        join_room(room_name)
        print(f"[JOIN] Utilisateur {current_user_id} a rejoint la room : {room_name}")

    # -------------------------------------------------------------------------
    # Quitter une discussion privée
    # -------------------------------------------------------------------------

    @socketio.on('leave_chat')
    def handle_leave_chat(data):
        """
        Reçoit : conversation_id
        """
        if 'user_id' not in session:  # CORRIGÉ : Session
            emit('error', {'message': 'Non authentifié'})
            return

        conversation_id = data.get('conversation_id')

        if not conversation_id:
            emit('error', {'message': 'conversation_id manquant'})
            return

        room_name = _build_room_name(conversation_id)
        leave_room(room_name)
        print(f"[LEAVE] Utilisateur {session['user_id']} a quitté la room : {room_name}")

    # -------------------------------------------------------------------------
    # Envoi d'un message
    # -------------------------------------------------------------------------

    @socketio.on('send_message')
    def handle_send_message(data):
        """
        Reçoit : conversation_id, contact_id, content
        Vérifie le matching avant toute sauvegarde.
        """
        if 'user_id' not in session:  # CORRIGÉ : Session
            emit('error', {'message': 'Non authentifié'})
            return

        conversation_id = data.get('conversation_id')
        contact_id = data.get('contact_id')
        content = data.get('content', '').strip()

        if not conversation_id or not contact_id or not content:
            emit('error', {'message': 'conversation_id, contact_id et content sont obligatoires'})
            return

        sender_id = session['user_id']  # CORRIGÉ : Session

        # Vérification d'autorisation avant sauvegarde
        match = (
            get_matching_by_users(sender_id, contact_id) or
            get_matching_by_users(contact_id, sender_id)
        )

        if not match:
            emit('error', {'message': 'Accès refusé : aucun matching actif'})
            print(f"[SECURITY] user:{sender_id} a tenté d'envoyer un message sans matching valide")
            return

        # CORRIGÉ : Remplacement du modèle externe par l'insertion PyMySQL standard du projet
        connexion = None
        curseur = None
        try:
            connexion = get_db_connection()
            curseur = connexion.cursor()
            
            requete = """
                INSERT INTO messages (conversation_id, expediteur_id, contenu)
                VALUES (%s, %s, %s)
            """
            curseur.execute(requete, (conversation_id, sender_id, content))
            connexion.commit()
            msg_id = curseur.lastrowid
            
        except Exception as e:
            if connexion:
                connexion.rollback()
            print(f"[ERROR] Sauvegarde BDD : {e}")
            emit('error', {'message': 'Erreur lors de la sauvegarde du message'})
            return
        finally:
            if curseur:
                curseur.close()
            if connexion:
                connexion.close()

        timestamp = datetime.now(timezone.utc).isoformat()
        room_name = _build_room_name(conversation_id)

        message_payload = {
            'id': msg_id,
            'conversation_id': conversation_id,
            'sender_id': sender_id,
            'content': content,
            'timestamp': timestamp,
        }

        emit('receive_message', message_payload, to=room_name)
        emit('message_sent', {'status': 'ok', 'id': msg_id, 'timestamp': timestamp}, to=request.sid)
        print(f"[MSG] user:{sender_id} → conv:{conversation_id} | {content[:50]}")


# -----------------------------------------------------------------------------
# Utilitaire
# -----------------------------------------------------------------------------

def _build_room_name(conversation_id) -> str:
    return f"room_conv_{conversation_id}"