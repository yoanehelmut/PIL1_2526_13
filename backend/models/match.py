# ==============================================================================
# PROJET MENTORLINK (PIL_2526_13)
# Fichier : backend/models/match.py
# Rôle : Gestion des correspondances mentor-étudiant
# ==============================================================================

import mysql.connector
from config.database import get_db_connection


def create_matching(etudiant_id, mentor_id, score):
    """
    Crée une nouvelle correspondance mentor-étudiant.
    """
    conn = None
    cur = None

    query = """
        INSERT INTO matchings
        (etudiant_id, mentor_id, score)
        VALUES (%s, %s, %s);
    """

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(query, (etudiant_id, mentor_id, score))
        conn.commit()

        return cur.lastrowid

    except mysql.connector.Error as db_error:
        if conn:
            conn.rollback()
        print(f"[ERROR SQL] {db_error.msg}")
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_matching_by_student(etudiant_id):
    """
    Retourne les correspondances d'un étudiant.
    """
    conn = None
    cur = None

    query = """
        SELECT *
        FROM matchings
        WHERE etudiant_id = %s;
    """

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute(query, (etudiant_id,))

        return cur.fetchall()

    except mysql.connector.Error as db_error:
        print(f"[ERROR SQL] {db_error.msg}")
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def update_matching_status(matching_id, statut):
    """
    Met à jour le statut d'un matching.
    """
    conn = None
    cur = None

    query = """
        UPDATE matchings
        SET statut = %s
        WHERE id = %s;
    """

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(query, (statut, matching_id))
        conn.commit()

        return True

    except mysql.connector.Error as db_error:
        if conn:
            conn.rollback()
        print(f"[ERROR SQL] {db_error.msg}")
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_matching_by_users(etudiant_id, mentor_id):
    """
    Vérifie qu'un matching accepté existe entre un étudiant et un mentor.
    Utilisé par chat.py pour autoriser l'accès à une conversation.
    Retourne le matching si trouvé, None sinon.
    """
    conn = None
    cur = None

    query = """
        SELECT id
        FROM matchings
        WHERE etudiant_id = %s
          AND mentor_id = %s
          AND statut = 'accepté'
        LIMIT 1;
    """

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute(query, (etudiant_id, mentor_id))

        return cur.fetchone()  # None si aucun match valide

    except mysql.connector.Error as db_error:
        print(f"[ERROR SQL] {db_error.msg}")
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()