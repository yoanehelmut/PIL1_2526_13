# ==============================================================================
# PROJET MENTORLINK (PIL1_2526_13) - COUCHE MODÈLE (ACCÈS AUX DONNÉES)
# Fichier : backend/models/user.py
# Rôle : Requêtes SQL adaptées STRICTEMENT à la table 'users' sous MySQL
# ==============================================================================

import mysql.connector
from mysql.connector import Error
import logging
from config.database import get_db_connection

# Configuration du journal de traçabilité (Logs) pour la production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_user(nom, prenom, email, mot_de_passe_hash, role, filiere=None, niveau=None):
    """
    Insère un nouvel utilisateur (étudiant ou mentor) dans la base de données MySQL.
    """
    # Initialisation des variables de connexion à vide pour le bloc 'finally'
    connexion_serveur_mysql = None
    curseur_execution_sql = None
    
    # Écriture de la requête SQL avec des marqueurs de sécurité %s
    requete_insertion_sql = """
        INSERT INTO users (nom, prenom, email, mot_de_passe_hash, role, filiere, niveau)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    
    try:
        # Établissement de la connexion réseau avec MySQL
        connexion_serveur_mysql = get_db_connection()
        
        # Création du curseur (notre outil pour envoyer les ordres SQL)
        curseur_execution_sql = connexion_serveur_mysql.cursor()
        
        # Exécution de la requête en injectant proprement les variables de l'utilisateur
        curseur_execution_sql.execute(
            requete_insertion_sql, 
            (nom, prenom, email, mot_de_passe_hash, role, filiere, niveau)
        )
        
        # Validation définitive de l'écriture des données sur le disque dur (Commit)
        connexion_serveur_mysql.commit()
        
        # Récupération de l'identifiant unique généré par l'AUTO_INCREMENT de MySQL
        identifiant_utilisateur_cree = curseur_execution_sql.lastrowid
        
        logging.info(f"[PROD] Utilisateur créé avec succès - ID Réel: {identifiant_utilisateur_cree} - Rôle: {role}")
        return identifiant_utilisateur_cree
        
    except mysql.connector.Error as erreur_base_de_donnees:
        # En cas d'échec, si le tuyau de connexion est ouvert, on annule tout (Rollback)
        if connexion_serveur_mysql:
            connexion_serveur_mysql.rollback()
            
        # Code 1062 = Violation de contrainte UNIQUE (L'email existe déjà)
        if erreur_base_de_donnees.errno == 1062:
            logging.warning(f"[PROD CONFLIT] L'adresse email '{email}' est déjà enregistrée dans la table users.")
        else:
            logging.error(f"[PROD ERREUR SQL] Échec de l'insertion : {erreur_base_de_donnees.msg}")
        return None
        
    finally:
        # Nettoyage systématique des ressources pour éviter de saturer le serveur MySQL
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()


def get_user_by_email(email):
    """
    Recherche un utilisateur dans la table MySQL à partir de son adresse e-mail.
    """
    connexion_serveur_mysql = None
    curseur_execution_sql = None
    
    requete_selection_sql = """
        SELECT id, nom, prenom, email, mot_de_passe_hash, role, filiere, niveau 
        FROM users 
        WHERE email = %s;
    """
    
    try:
        connexion_serveur_mysql = get_db_connection()
        
        # 'dictionary=True' permet de récupérer le résultat sous forme de dictionnaire Python
        curseur_execution_sql = connexion_serveur_mysql.cursor(dictionary=True)
        
        # Exécution de la recherche
        curseur_execution_sql.execute(requete_selection_sql, (email,))
        
        # Récupération de la ligne correspondante (renvoie un dictionnaire ou None)
        dictionnaire_donnees_utilisateur = curseur_execution_sql.fetchone()
        
        if dictionnaire_donnees_utilisateur:
            logging.info(f"[PROD SUCCESS] Compte utilisateur localisé pour l'email : {email}")
            return dictionnaire_donnees_utilisateur
        else:
            logging.info(f"[PROD INFO] Aucun compte ne correspond à l'email : {email}")
            return None
            
    except mysql.connector.Error as erreur_base_de_donnees:
        logging.error(f"[PROD ERREUR SQL] Échec de la recherche par email : {erreur_base_de_donnees.msg}")
        return None
        
    finally:
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()


def update_password_reset_token(email, token_securise):
    """
    Enregistre le jeton temporaire de récupération de mot de passe envoyé par mail.
    """
    connexion_serveur_mysql = None
    curseur_execution_sql = None
    
    requete_mise_a_jour_token_sql = """
        UPDATE users 
        SET reset_token = %s, reset_token_expires = DATE_ADD(NOW(), INTERVAL 1 HOUR)
        WHERE email = %s;
    """
    try:
        connexion_serveur_mysql = get_db_connection()
        curseur_execution_sql = connexion_serveur_mysql.cursor()
        
        curseur_execution_sql.execute(requete_mise_a_jour_token_sql, (token_securise, email))
        connexion_serveur_mysql.commit()
        
        # Renvoie True si au moins une ligne de la base a été modifiée
        return curseur_execution_sql.rowcount > 0
        
    except mysql.connector.Error as erreur_base_de_donnees:
        if connexion_serveur_mysql:
            connexion_serveur_mysql.rollback()
        logging.error(f"[PROD ERREUR SQL] Impossible d'enregistrer le token de récupération : {erreur_base_de_donnees.msg}")
        return False
        
    finally:
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()


def update_user_password(token_securise, nouveau_mot_de_passe_hash):
    """
    Vérifie la validité du jeton et applique le nouveau mot de passe haché.
    """
    connexion_serveur_mysql = None
    curseur_execution_sql = None
    
    requete_changement_mot_de_passe_sql = """
        UPDATE users 
        SET mot_de_passe_hash = %s, reset_token = NULL, reset_token_expires = NULL
        WHERE reset_token = %s AND reset_token_expires > NOW();
    """
    try:
        connexion_serveur_mysql = get_db_connection()
        curseur_execution_sql = connexion_serveur_mysql.cursor()
        
        curseur_execution_sql.execute(
            requete_changement_mot_de_passe_sql, 
            (nouveau_mot_de_passe_hash, token_securise)
        )
        connexion_serveur_mysql.commit()
        
        if curseur_execution_sql.rowcount > 0:
            logging.info("[PROD SUCCESS] Le mot de passe a été modifié avec succès en base de données.")
            return True
        else:
            logging.warning("[PROD SECURITE] Tentative d'utilisation d'un token invalide ou expiré.")
            return False
            
    except mysql.connector.Error as erreur_base_de_donnees:
        if connexion_serveur_mysql:
            connexion_serveur_mysql.rollback()
        logging.error(f"[PROD ERREUR SQL] Échec de la mise à jour du mot de passe : {erreur_base_de_donnees.msg}")
        return False
        
    finally:
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()
