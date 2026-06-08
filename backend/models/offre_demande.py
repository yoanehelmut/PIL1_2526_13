# ==============================================================================
# PROJET MENTORLINK (PIL_2526_13)
# Fichier : backend/models/offre_demande.py
# Rôle : Gestion des offres et demandes de mentorat
# ==============================================================================

import mysql.connector
from config.database import get_db_connection


def create_offre_demande(user_id, type_, description):
    """
    Crée une offre ou une demande de mentorat.
    """

    conn = None
    cur = None

    query = """
        INSERT INTO offres_demandes
        (user_id, type, description)
        VALUES (%s, %s, %s);
    """

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            query,
            (user_id, type_, description)
        )

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


def get_all_offres_demandes():
    """
    Retourne toutes les offres et demandes.
    """

    conn = None
    cur = None

    query = """
        SELECT *
        FROM offres_demandes
        ORDER BY created_at DESC;
    """

    try:

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute(query)

        return cur.fetchall()

    except mysql.connector.Error as db_error:

        print(f"[ERROR SQL] {db_error.msg}")
        return []

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


def get_offres_demandes_by_user(user_id):
    """
    Retourne les offres/demandes d'un utilisateur.
    """

    conn = None
    cur = None

    query = """
        SELECT *
        FROM offres_demandes
        WHERE user_id = %s
        ORDER BY created_at DESC;
    """

    try:

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute(query, (user_id,))

        return cur.fetchall()

    except mysql.connector.Error as db_error:

        print(f"[ERROR SQL] {db_error.msg}")
        return []

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()