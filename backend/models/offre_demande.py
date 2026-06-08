import mysql.connector
from mysql.connector import Error
import logging
from config.database import get_db_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_offre_demande(user_id, type_offre, description=None):
    """
    Insère une nouvelle offre ou demande dans la table 'offres_demandes'.
    type_offre accepte uniquement : 'offre' ou 'demande'.
    """
    connexion_serveur_mysql = None
    curseur_execution_sql = None

    # Vérification que le type est valide avant d'envoyer à la BDD
    if type_offre not in ('offre', 'demande'):
        logging.error(f"[PROD ERREUR] Type invalide : {type_offre}. Valeurs acceptées : 'offre' ou 'demande'.")
        return None

    requete_insertion_sql = """
        INSERT INTO offres_demandes (user_id, type, description)
        VALUES (%s, %s, %s);
    """

    try:
        connexion_serveur_mysql = get_db_connection()
        curseur_execution_sql = connexion_serveur_mysql.cursor()

        curseur_execution_sql.execute(
            requete_insertion_sql,
            (user_id, type_offre, description)
        )
        connexion_serveur_mysql.commit()

        identifiant_cree = curseur_execution_sql.lastrowid
        logging.info(f"[PROD] Nouvelle {type_offre} créée - ID: {identifiant_cree} - User: {user_id}")
        return identifiant_cree

    except mysql.connector.Error as erreur_base_de_donnees:
        if connexion_serveur_mysql:
            connexion_serveur_mysql.rollback()
        logging.error(f"[PROD ERREUR SQL] Échec création offre/demande : {erreur_base_de_donnees.msg}")
        return None

    finally:
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()


def get_offre_demande_by_id(offre_demande_id):
    """
    Récupère une offre/demande avec les infos de son auteur (JOIN avec users).
    """
    connexion_serveur_mysql = None
    curseur_execution_sql = None

    requete_selection_sql = """
        SELECT od.id, od.user_id, od.type, od.description, od.created_at,
               u.nom, u.prenom, u.role, u.filiere, u.niveau
        FROM offres_demandes od
        JOIN users u ON od.user_id = u.id
        WHERE od.id = %s;
    """

    try:
        connexion_serveur_mysql = get_db_connection()
        curseur_execution_sql = connexion_serveur_mysql.cursor(dictionary=True)

        curseur_execution_sql.execute(requete_selection_sql, (offre_demande_id,))
        resultat = curseur_execution_sql.fetchone()

        if resultat:
            logging.info(f"[PROD SUCCESS] Offre/demande récupérée - ID: {offre_demande_id}")
            return resultat
        else:
            logging.info(f"[PROD INFO] Aucune offre/demande trouvée - ID: {offre_demande_id}")
            return None

    except mysql.connector.Error as erreur_base_de_donnees:
        logging.error(f"[PROD ERREUR SQL] Impossible de récupérer l'offre/demande : {erreur_base_de_donnees.msg}")
        return None

    finally:
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()


def get_all_offres_demandes(type_filtre=None):
    """
    Récupère toutes les offres/demandes.
    Si type_filtre = 'offre' → uniquement les offres.
    Si type_filtre = 'demande' → uniquement les demandes.
    Si type_filtre = None → tout récupérer.
    """
    connexion_serveur_mysql = None
    curseur_execution_sql = None

    if type_filtre:
        requete_selection_sql = """
            SELECT od.id, od.user_id, od.type, od.description, od.created_at,
                   u.nom, u.prenom, u.role, u.filiere, u.niveau
            FROM offres_demandes od
            JOIN users u ON od.user_id = u.id
            WHERE od.type = %s
            ORDER BY od.created_at DESC;
        """
        parametres = (type_filtre,)
    else:
        requete_selection_sql = """
            SELECT od.id, od.user_id, od.type, od.description, od.created_at,
                   u.nom, u.prenom, u.role, u.filiere, u.niveau
            FROM offres_demandes od
            JOIN users u ON od.user_id = u.id
            ORDER BY od.created_at DESC;
        """
        parametres = ()

    try:
        connexion_serveur_mysql = get_db_connection()
        curseur_execution_sql = connexion_serveur_mysql.cursor(dictionary=True)

        curseur_execution_sql.execute(requete_selection_sql, parametres)
        liste_resultats = curseur_execution_sql.fetchall()

        logging.info(f"[PROD SUCCESS] {len(liste_resultats)} offre(s)/demande(s) récupérée(s).")
        return liste_resultats

    except mysql.connector.Error as erreur_base_de_donnees:
        logging.error(f"[PROD ERREUR SQL] Impossible de récupérer les offres/demandes : {erreur_base_de_donnees.msg}")
        return []

    finally:
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()


def get_offres_demandes_by_user(user_id):
    """
    Récupère toutes les offres et demandes d'un utilisateur spécifique.
    """
    connexion_serveur_mysql = None
    curseur_execution_sql = None

    requete_selection_sql = """
        SELECT id, user_id, type, description, created_at
        FROM offres_demandes
        WHERE user_id = %s
        ORDER BY created_at DESC;
    """

    try:
        connexion_serveur_mysql = get_db_connection()
        curseur_execution_sql = connexion_serveur_mysql.cursor(dictionary=True)

        curseur_execution_sql.execute(requete_selection_sql, (user_id,))
        liste_resultats = curseur_execution_sql.fetchall()

        logging.info(f"[PROD SUCCESS] {len(liste_resultats)} offre(s)/demande(s) pour User ID: {user_id}")
        return liste_resultats

    except mysql.connector.Error as erreur_base_de_donnees:
        logging.error(f"[PROD ERREUR SQL] Impossible de récupérer les offres/demandes : {erreur_base_de_donnees.msg}")
        return []

    finally:
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()


def delete_offre_demande(offre_demande_id, user_id):
    """
    Supprime une offre/demande uniquement si elle appartient à l'utilisateur demandeur.
    """
    connexion_serveur_mysql = None
    curseur_execution_sql = None

    requete_suppression_sql = """
        DELETE FROM offres_demandes
        WHERE id = %s AND user_id = %s;
    """

    try:
        connexion_serveur_mysql = get_db_connection()
        curseur_execution_sql = connexion_serveur_mysql.cursor()

        curseur_execution_sql.execute(requete_suppression_sql, (offre_demande_id, user_id))
        connexion_serveur_mysql.commit()

        if curseur_execution_sql.rowcount > 0:
            logging.info(f"[PROD SUCCESS] Offre/demande ID {offre_demande_id} supprimée par User ID {user_id}.")
            return True
        else:
            logging.warning(f"[PROD SECURITE] Suppression refusée : ID {offre_demande_id} n'appartient pas au User ID {user_id}.")
            return False

    except mysql.connector.Error as erreur_base_de_donnees:
        if connexion_serveur_mysql:
            connexion_serveur_mysql.rollback()
        logging.error(f"[PROD ERREUR SQL] Échec suppression : {erreur_base_de_donnees.msg}")
        return False

    finally:
        if curseur_execution_sql:
            curseur_execution_sql.close()
        if connexion_serveur_mysql:
            connexion_serveur_mysql.close()