import pymysql
from config.database import get_db_connection

def sauvegarder_message(conversation_id, expediteur_id, contenu):
    """
    Insère un nouveau message dans la base de données.
    Gère proprement le commit (validation) et le rollback en cas d'erreur.
    """
    connexion = None
    curseur = None
    try:
        connexion = get_db_connection()
        curseur = connexion.cursor(pymysql.cursors.DictCursor)
        
        requete = """
            INSERT INTO messages (conversation_id, expediteur_id, contenu) 
            VALUES (%s, %s, %s)
        """
        curseur.execute(requete, (conversation_id, expediteur_id, contenu))
        connexion.commit()
        
        # Récupère l'ID du message qui vient d'être généré par MySQL
        message_id = curseur.lastrowid
        return {"id": message_id}
        
    except Exception as e:
        if connexion:
            connexion.rollback()
        raise e
    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()


def obtenir_conversation(conversation_id):
    """
    Récupère l'historique complet des messages d'une conversation spécifique.
    Trié du plus ancien au plus récent pour le fil de discussion.
    """
    connexion = None
    curseur = None
    try:
        connexion = get_db_connection()
        curseur = connexion.cursor(pymysql.cursors.DictCursor)
        
        # CORRECTION : Utilisation de 'timestamp' à la place de 'date_envoi' pour correspondre à database.sql
        requete = """
            SELECT id, conversation_id, expediteur_id, contenu, timestamp 
            FROM messages 
            WHERE conversation_id = %s 
            ORDER BY timestamp ASC
        """
        curseur.execute(requete, (conversation_id,))
        lignes = curseur.fetchall()
        
        # Formatage propre en dictionnaire pour le renvoyer facilement au frontend
        messages = []
        for ligne in lignes:
            messages.append({
                "id": ligne["id"],
                "conversation_id": ligne["conversation_id"],
                "expediteur_id": ligne["expediteur_id"],
                "contenu": ligne["contenu"],
                "timestamp": str(ligne["timestamp"])  # Conversion en chaîne pour éviter les bugs de sérialisation JSON
            })
        return messages
        
    except Exception as e:
        raise e
    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()