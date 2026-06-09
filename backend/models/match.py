import pymysql
from config.database import get_db_connection


def create_matching(etudiant_id, mentor_id, score):
    """
    Crée une nouvelle correspondance mentor-étudiant.
    """
    connexion = None
    curseur = None

    query = """
        INSERT INTO matchings (etudiant_id, mentor_id, score)
        VALUES (%s, %s, %s);
    """

    try:
        connexion = get_db_connection()
        curseur = connexion.cursor(pymysql.cursors.DictCursor)

        curseur.execute(query, (etudiant_id, mentor_id, score))
        connexion.commit()

        return curseur.lastrowid

    except Exception as db_error:
        if connexion:
            connexion.rollback()
        print(f"[ERROR SQL] {str(db_error)}")
        return None

    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()


def get_matching_by_student(etudiant_id):
    """
    Retourne les correspondances d'un étudiant.
    """
    connexion = None
    curseur = None

    query = """
        SELECT id, etudiant_id, mentor_id, score, statut, created_at, updated_at
        FROM matchings
        WHERE etudiant_id = %s;
    """

    try:
        connexion = get_db_connection()
        curseur = connexion.cursor(pymysql.cursors.DictCursor)

        curseur.execute(query, (etudiant_id,))
        return curseur.fetchall()

    except Exception as db_error:
        print(f"[ERROR SQL] {str(db_error)}")
        return []

    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()


def update_matching_status(matching_id, statut):
    """
    Met à jour le statut d'un matching.
    """
    connexion = None
    curseur = None

    query = """
        UPDATE matchings
        SET statut = %s
        WHERE id = %s;
    """

    try:
        connexion = get_db_connection()
        curseur = connexion.cursor(pymysql.cursors.DictCursor)

        # Sécurité : On s'assure que le statut envoyé est en minuscules et sans accents indésirables
        statut_formate = statut.lower().replace('é', 'e')

        curseur.execute(query, (statut_formate, matching_id))
        connexion.commit()
        return True

    except Exception as db_error:
        if connexion:
            connexion.rollback()
        print(f"[ERROR SQL] {str(db_error)}")
        return False

    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()


def get_matching_by_users(etudiant_id, mentor_id):
    """
    Vérifie qu'un matching accepté existe entre un étudiant et un mentor.
    Utilisé par le système de messagerie pour autoriser l'accès à une conversation.
    Retourne le matching si trouvé, None sinon.
    """
    connexion = None
    curseur = None

    query = """
        SELECT id
        FROM matchings
        WHERE etudiant_id = %s
          AND mentor_id = %s
          AND statut = 'accepte'
        LIMIT 1;
    """

    try:
        connexion = get_db_connection()
        curseur = connexion.cursor(pymysql.cursors.DictCursor)

        curseur.execute(query, (etudiant_id, mentor_id))
        return curseur.fetchone()  # Renvoie le dictionnaire ou None si aucun match valide

    except Exception as db_error:
        print(f"[ERROR SQL] {str(db_error)}")
        return None

    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()