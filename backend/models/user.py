# ==============================================================================
# PROJET MENTORLINK (PIL_2526_13) - COUCHE MODÈLE (DONNÉES)
# Fichier : backend/models/user.py
# Rôle : Requêtes SQL pour la table 'users' sous MySQL (Inscription, Connexion, Réinitialisation)
# ==============================================================================

import mysql.connector
from config.database import get_db_connection

def get_user_by_email(email):
    """
    Recherche un utilisateur par son e-mail.
    Permet de vérifier si le compte existe avant une connexion ou une réinitialisation.
    """
    conn = None
    cur = None
    query = """
    SELECT id, name, email, password_hash, role 
    FROM users 
    WHERE email = %s;
    """
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True) # Retourne un dictionnaire pratique
        cur.execute(query, (email,))
        user = cur.fetchone()
        return user
    except mysql.connector.Error as db_error:
        print(f"[ERROR SQL] Erreur lors de la recherche de l'email : {db_error.msg}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()

def create_user(name, email, password_hash, role):
    existing = get_user_by_email(email)
    if existing:
        return None
    """
    Insère un nouvel utilisateur lors de l'inscription.
    """
    conn = None
    cur = None
    query = """
        INSERT INTO users (name, email, password_hash, role)
        VALUES (%s, %s, %s, %s);
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, (name, email, password_hash, role))
        conn.commit()
        return cur.lastrowid
    except mysql.connector.Error as db_error:
        if conn: conn.rollback()
        print(f"[ERROR SQL] Échec de la création de l'utilisateur : {db_error.msg}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()

def update_password_reset_token(email, token):
    """
    Enregistre le jeton (token) généré et définit une expiration (ex: +1 heure).
    """
    conn = None
    cur = None
    # Remarque : assurez-vous d'avoir les colonnes reset_token et reset_token_expires dans MySQL
    query = """
        UPDATE users 
        SET reset_token = %s, reset_token_expires = DATE_ADD(NOW(), INTERVAL 1 HOUR)
        WHERE email = %s;
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, (token, email))
        conn.commit()
        return cur.rowcount > 0
    except mysql.connector.Error as db_error:
        if conn: conn.rollback()
        print(f"[ERROR SQL] Impossible d'enregistrer le token : {db_error.msg}")
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()
