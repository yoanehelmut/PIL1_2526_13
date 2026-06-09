import os
import re
import pymysql
from flask import Blueprint, request, jsonify, session
from config.database import get_db_connection

profile_bp = Blueprint('profile', __name__)

# Valeurs autorisées
NIVEAUX_VALIDES = ['L1', 'L2', 'L3', 'M1', 'M2']
FILIERES_VALIDES = ['Informatique', 'Mathématiques', 'Physique', 'Économie', 'Droit']
BIO_MAX_LENGTH = 500
TELEPHONE_MAX_LENGTH = 20


# ── Info-utilisateur ──────────────────────────────────────────────────────────────

def get_user_from_db(user_id):
    """Récupère les infos d'un utilisateur depuis la BDD."""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT nom, prenom, email, telephone, filiere, niveau, bio, photo, role 
            FROM users WHERE id = %s
        """, (user_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


# CORRECTION 4 : une seule connexion BDD pour compétences et lacunes
def get_competences_lacunes(user_id):
    """Récupère les compétences et lacunes d'un utilisateur."""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT matiere, type FROM competences WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()

        competences = [row['matiere'] for row in rows if row['type'] == 'fort']
        lacunes     = [row['matiere'] for row in rows if row['type'] == 'faible']

        return competences, lacunes
    finally:
        cursor.close()
        conn.close()


# ── Routes ───────────────────────────────────────────────────────────────────

@profile_bp.route('/me', methods=['GET'])
def view_my_profile():
    """Affiche le profil complet de l'utilisateur connecté."""
    if 'user_id' not in session:
        return jsonify({"message": "Veuillez vous connecter pour accéder à votre profil."}), 401

    user_id = session['user_id']

    try:
        user = get_user_from_db(user_id)

        if not user:
            return jsonify({"message": "Utilisateur introuvable."}), 404

        # Gestion du cas où photo est None
        user['photo'] = user.get('photo') or ''

        competences, lacunes = get_competences_lacunes(user_id)

        return jsonify({
            "user": user,
            "competences": competences,
            "lacunes": lacunes
        }), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500


@profile_bp.route('/edit', methods=['POST'])
def edit_profile():
    """Permet à l'utilisateur de modifier ses informations de profil."""
    if 'user_id' not in session:
        return jsonify({"message": "Non autorisé. Veuillez vous connecter."}), 401

    user_id = session['user_id']

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Données JSON invalides ou manquantes."}), 400

    nom       = data.get('nom', '').strip()
    prenom    = data.get('prenom', '').strip()
    filiere   = data.get('filiere', None)
    niveau    = data.get('niveau', None)
    bio       = data.get('bio', '').strip()
    telephone = data.get('telephone', '').strip()
    photo     = data.get('photo', '').strip()        # CORRECTION 1 : ajout photo
    email     = data.get('email', '').strip()        # CORRECTION 5 : ajout email

    # ── Validations ──────────────────────────────────────────────────────────
    if not nom or not prenom:
        return jsonify({"message": "Le nom et le prénom sont obligatoires."}), 400

    if len(bio) > BIO_MAX_LENGTH:
        return jsonify({"message": f"La bio ne doit pas dépasser {BIO_MAX_LENGTH} caractères."}), 400

    if len(telephone) > TELEPHONE_MAX_LENGTH:
        return jsonify({"message": "Numéro de téléphone invalide."}), 400

    if niveau and niveau not in NIVEAUX_VALIDES:
        return jsonify({"message": f"Niveau invalide. Valeurs acceptées : {', '.join(NIVEAUX_VALIDES)}"}), 400

    if filiere and filiere not in FILIERES_VALIDES:
        return jsonify({"message": f"Filière invalide. Valeurs acceptées : {', '.join(FILIERES_VALIDES)}"}), 400

    # CORRECTION 5 : validation du format email
    if email:
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        if not re.match(email_regex, email):
            return jsonify({"message": "Adresse email invalide."}), 400

    # ── Mise à jour en BDD ───────────────────────────────────────────────────
    # CORRECTION 4 : une seule connexion BDD pour tout le bloc
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # CORRECTION 2 : ajout photo et CORRECTION 5 : ajout email dans le UPDATE
        cursor.execute("""
            UPDATE users 
            SET nom = %s, prenom = %s, filiere = %s, niveau = %s, 
                bio = %s, telephone = %s, photo = %s, email = %s
            WHERE id = %s
        """, (nom, prenom, filiere, niveau, bio, telephone, photo, email, user_id))

        conn.commit()

        session['user_nom'] = nom
        session['user_prenom'] = prenom

        return jsonify({"message": "Profil mis à jour avec succès !"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Erreur lors de la mise à jour : {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# ── CORRECTION 3 : Route pour modifier les compétences et lacunes ─────────────

@profile_bp.route('/competences/edit', methods=['POST'])
def edit_competences():
    """Permet à l'utilisateur de modifier ses compétences et lacunes."""
    if 'user_id' not in session:
        return jsonify({"message": "Non autorisé. Veuillez vous connecter."}), 401

    user_id = session['user_id']

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Données JSON invalides ou manquantes."}), 400

    competences = data.get('competences', [])
    lacunes     = data.get('lacunes', [])

    if not isinstance(competences, list) or not isinstance(lacunes, list):
        return jsonify({"message": "Les compétences et lacunes doivent être des listes."}), 400

    # CORRECTION 4 : une seule connexion BDD
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Supprimer les anciennes entrées
        cursor.execute("DELETE FROM competences WHERE user_id = %s", (user_id,))

        # Insérer les nouvelles compétences
        for matiere in competences:
            cursor.execute(
                "INSERT INTO competences (user_id, matiere, type) VALUES (%s, %s, 'fort')",
                (user_id, matiere.strip())
            )

        # Insérer les nouvelles lacunes
        for matiere in lacunes:
            cursor.execute(
                "INSERT INTO competences (user_id, matiere, type) VALUES (%s, %s, 'faible')",
                (user_id, matiere.strip())
            )

        conn.commit()
        return jsonify({"message": "Compétences mises à jour avec succès !"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Erreur lors de la mise à jour : {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()