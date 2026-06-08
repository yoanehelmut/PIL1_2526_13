# PROJET MENTORLINK (PIL1_2526_13)
# Fichier : backend/models/message.py
# Rôle : Accès base de données (Requêtes SQL) pour les messages

import pymysql
from config.database import get_db_connection

def sauvegarder_message(conversation_id, expediteur_id, contenu):
    """Insère un nouveau message dans la base de données."""
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        query = """
            INSERT INTO messages (conversation_id, expediteur_id, contenu) 
            VALUES (%s, %s, %s)
        """
        cur.execute(query, (conversation_id, expediteur_id, contenu))
        conn.commit()
        
        # Récupère l'ID du message qui vient d'être généré par MySQL
        msg_id = cur.lastrowid
        return {"id": msg_id}
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def obtenir_conversation(conversation_id):
    """Récupère l'historique complet des messages d'une conversation spécifique."""
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Trié du plus ancien au plus récent pour le fil de discussion
        query = """
            SELECT id, conversation_id, expediteur_id, contenu, date_envoi 
            FROM messages 
            WHERE conversation_id = %s 
            ORDER BY date_envoi ASC
        """
        cur.execute(query, (conversation_id,))
        rows = cur.fetchall()
        
        # Formatage propre en dictionnaire pour le renvoyer facilement au frontend
        messages = []
        for r in rows:
            messages.append({
                "id": r["id"],
                "conversation_id": r["conversation_id"],
                "expediteur_id": r["expediteur_id"],
                "contenu": r["contenu"],
                "date_envoi": str(r["date_envoi"])  # Converti en chaîne pour éviter les bugs JSON avec le type DateTime
            })
        return messages
        
    except Exception as e:
        raise e
    finally:
        cur.close()
        conn.close()