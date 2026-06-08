# ==============================================================================
# PROJET MENTORLINK (PIL1_2526_13) - COUCHE MODÈLE (ACCÈS AUX DONNÉES)
# Fichier : backend/models/user.py
# Rôle : Requêtes SQL adaptées STRICTEMENT à la table 'users' de production
# ==============================================================================

import mysql.connector
from mysql.connector import Error
import logging
from config.database import get_db_connection

# Configuration du système de journalisation (Logs) pour suivre l'activité en production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_user(nom, prenom, email, mot_de_passe_hash, role, filiere=None, niveau=None):
    """
    Insère un nouvel utilisateur (étudiant ou mentor) dans la table 'users'.
    S'aligne parfaitement sur les colonnes de la base de données de production.
    """
    # [COMMENTAIRE] Initialisation des variables à vide pour pouvoir les manipuler et les fermer dans le bloc 'finally'
    connexion_serveur_mysql = None
    curseur_execution_sql = None
    
    # [COMMENTAIRE] Préparation de la requête SQL d'insertion. 
    # Les marqueurs %s protègent le projet contre les attaques par injection SQL.
    requete_insertion_sql = """
        INSERT INTO users (nom, prenom, email, mot_de_passe_hash, role, filiere, niveau)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    
    try:
        # [COMMENTAIRE] Connexion active au serveur de base de données MySQL via le module partagé
        connexion_serveur_mysql = get_db_connection()
        
        # [COMMENTAIRE] Création du curseur, l'outil Python qui transmet les ordres SQL au serveur
        curseur_execution_sql = connexion_serveur_mysql.cursor()
        
        # [COMMENTAIRE] Exécution de la commande SQL en injectant de façon sécurisée les variables reçues du Frontend
        curseur_execution_sql.execute(
            requete_insertion_sql, 
            (nom, prenom, email, mot_de_passe_hash, role, filiere, niveau)
        )
        
        # [COMMENTAIRE] Validation obligatoire (Commit) pour enregistrer définitivement le membre sur le disque dur
        connexion_serveur_mysql.commit()
        
        # [COMMENTAIRE] Récupération de l'identifiant unique (ID) généré automatiquement par le champ INT AUTO_INCREMENT
        identifiant_utilisateur_cree = curseur_execution_sql.lastrowid
        
        # [COMMENTAIRE] Journalisation du succès dans les logs de production
        logging.info(f"[PROD] Nouvel utilisateur enregistré avec succès - ID Réel: {identifiant_utilisateur_cree} - Rôle: {role}")
        return identifiant_utilisateur_cree
        
    except mysql.connector.Error as erreur_base_de_donnees:
        # [COMMENTAIRE] En cas d'erreur de communication ou de syntaxe, on annule l'action (Rollback) pour éviter les données corrompues
        if connexion_serveur_mysql:
            connexion_serveur_mysql.rollback()
            
        # [COMMENTAIRE] Traitement du code d'erreur MySQL 1062 qui correspond à un conflit d'unicité (l'email est déjà pris)
        if erreur_base_de_donnees.errno == 1062:
            logging.warning(f"[PROD CONFLIT] L'adresse email '{email}' est déjà associée à un compte existant.")
        else:
            logging.error(f"[PROD ERREUR SQL] Échec de la création de l'utilisateur : {erreur_base_de_donnees.msg}")
        return None
        
    finally:
        # [COMMENTAIRE] Libération systématique des connexions pour ne pas saturer et bloquer le serveur MySQL du projet
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()


def get_user_by_email(email):
    """
    Recherche et extrait l'intégralité du profil d'un utilisateur grâce à son e-mail.
    Indispensable pour l'algorithme de connexion et d'authentification (auth.py).
    """
    connexion_serveur_mysql = None
    curseur_execution_sql = None
    
    # [COMMENTAIRE] Sélection de l'ensemble des colonnes réelles définies dans ton script SQL, y compris le rôle
    requete_selection_sql = """
        SELECT id, nom, prenom, email, mot_de_passe_hash, role, filiere, niveau, reset_token, reset_token_expires, created_at, updated_at
        FROM users 
        WHERE email = %s;
    """
    
    try:
        connexion_serveur_mysql = get_db_connection()
        
        # [COMMENTAIRE] L'option 'dictionary=True' force MySQL à renvoyer les données sous forme de dictionnaire Python structuré
        curseur_execution_sql = connexion_serveur_mysql.cursor(dictionary=True)
        
        # [COMMENTAIRE] Envoi de la requête de recherche avec l'email ciblé
        curseur_execution_sql.execute(requete_selection_sql, (email,))
        
        # [COMMENTAIRE] Récupération de la ligne unique trouvée (renvoie le dictionnaire complet du profil, ou None s'il n'existe pas)
        dictionnaire_donnees_utilisateur = curseur_execution_sql.fetchone()
        
        if dictionnaire_donnees_utilisateur:
            logging.info(f"[PROD SUCCESS] Données de l'utilisateur récupérées pour l'email : {email}")
            return dictionnaire_donnees_utilisateur
        else:
            logging.info(f"[PROD INFO] Aucun utilisateur ne possède l'email : {email}")
            return None
            
    except mysql.connector.Error as erreur_base_de_donnees:
        logging.error(f"[PROD ERREUR SQL] Impossible de faire la recherche par email : {erreur_base_de_donnees.msg}")
        return None
        
    finally:
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()


def update_password_reset_token(email, token_securise):
    """
    Enregistre le jeton de sécurité généré pour la récupération de mot de passe par mail.
    Limite sa durée de validité à 1 heure grâce à la fonction de temps native de MySQL DATE_ADD.
    """
    connexion_serveur_mysql = None
    curseur_execution_sql = None
    
    # [COMMENTAIRE] Mise à jour des colonnes 'reset_token' et 'reset_token_expires' de notre table de production
    requete_mise_a_jour_token_sql = """
        UPDATE users 
        SET reset_token = %s, reset_token_expires = DATE_ADD(NOW(), INTERVAL 1 HOUR)
        WHERE email = %s;
    """
    try:
        connexion_serveur_mysql = get_db_connection()
        curseur_execution_sql = connexion_serveur_mysql.cursor()
        
        # [COMMENTAIRE] Exécution de la modification pour l'utilisateur qui a demandé le mail de récupération
        curseur_execution_sql.execute(requete_mise_a_jour_token_sql, (token_securise, email))
        connexion_serveur_mysql.commit()
        
        # [COMMENTAIRE] Retourne True si l'email existait bien et qu'une ligne a effectivement été modifiée (rowcount > 0)
        return curseur_execution_sql.rowcount > 0
        
    except mysql.connector.Error as erreur_base_de_donnees:
        if connexion_serveur_mysql:
            connexion_serveur_mysql.rollback()
        logging.error(f"[PROD ERREUR SQL] Échec de l'application du token de réinitialisation : {erreur_base_de_donnees.msg}")
        return False
        
    finally:
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()


def update_user_password(token_securise, nouveau_mot_de_passe_hash):
    """
    Vérifie la validité temporelle du token, applique le nouveau mot de passe haché
    et nettoie immédiatement les champs de récupération pour empêcher une réutilisation frauduleuse.
    """
    connexion_serveur_mysql = None
    curseur_execution_sql = None
    
    # [COMMENTAIRE] Sécurité de production stricte : le token doit correspondre ET l'heure actuelle (NOW()) 
    # doit être inférieure à la date d'expiration pour que le mot de passe soit changé.
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
        
        # [COMMENTAIRE] Si rowcount > 0, cela signifie que le jeton était valide, non expiré, et que la mise à jour s'est faite
        if curseur_execution_sql.rowcount > 0:
            logging.info("[PROD SUCCESS] Le mot de passe a été modifié avec succès et sécurisé en base de données.")
            return True
        else:
            logging.warning("[PROD SECURITE] Tentative de réinitialisation rejetée : Jeton expiré ou corrompu.")
            return False
            
    except mysql.connector.Error as erreur_base_de_donnees:
        if connexion_serveur_mysql:
            connexion_serveur_mysql.rollback