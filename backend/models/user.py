import pymysql
from config.database import get_db_connection

def create_user(nom, prenom, email, mot_de_passe_hash, role, filiere=None, niveau=None):
    """
    Insère un nouvel utilisateur dans la table 'users'.
    Gère proprement le commit (validation) et le rollback en cas d'erreur.
    """
    connexion = None
    curseur = None
    try:
        connexion = get_db_connection()
        curseur = connexion.cursor()
        
        # Sécurité pour l'ENUM de ta base de données : force les minuscules ('mentor' ou 'etudiant')
        role_formate = role.lower()
        
        requete = """
            INSERT INTO users (nom, prenom, email, mot_de_passe_hash, role, filiere, niveau)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        valeurs = (nom, prenom, email, mot_de_passe_hash, role_formate, filiere, niveau)
        
        curseur.execute(requete, valeurs)
        
        # TRÈS IMPORTANT : Puisque autocommit=False dans database.py, 
        # il faut obligatoirement valider l'insertion pour qu'elle s'écrive en base
        connexion.commit()
        
        # Retourne l'ID unique de l'utilisateur qui vient d'être créé
        return curseur.lastrowid

    except Exception as e:
        # En cas de bug (ex: doublon d'email), on annule tout pour ne pas corrompre la base
        if connexion:
            connexion.rollback()
        raise e
    finally:
        # On referme proprement le curseur et le tunnel MySQL
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()


def get_user_by_email(email):
    """
    Recherche un utilisateur par son email.
    Utile pour vérifier les doublons à l'inscription et valider la connexion (Login).
    """
    connexion = None
    curseur = None
    try:
        connexion = get_db_connection()
        curseur = connexion.cursor()
        
        requete = "SELECT * FROM users WHERE email = %s"
        curseur.execute(requete, (email,))
        
        # Récupère l'utilisateur sous forme de dictionnaire grâce à DictCursor
        utilisateur = curseur.fetchone()
        return utilisateur

    except Exception as e:
        raise e
    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()


def get_user_by_id(user_id):
    """
    Récupère le profil complet d'un utilisateur à partir de son ID.
    Utile pour afficher le profil de l'utilisateur connecté sur l'application.
    """
    connexion = None
    curseur = None
    try:
        connexion = get_db_connection()
        curseur = connexion.cursor()
        
        requete = "SELECT id, nom, prenom, email, role, filiere, niveau, created_at FROM users WHERE id = %s"
        curseur.execute(requete, (user_id,))
        
        utilisateur = curseur.fetchone()
        return utilisateur

    except Exception as e:
        raise e
    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()