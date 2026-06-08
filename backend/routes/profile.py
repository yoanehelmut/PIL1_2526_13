import os
import pymysql
from flask import Blueprint, request, jsonify, session
from config.database import get_db_connection

profile_bp = Blueprint('profile', __name__)

# Valeurs autorisées
NIVEAUX_VALIDES = ['L1', 'L2', 'L3', 'M1', 'M2']
FILIERES_VALIDES = ['Informatique', 'Mathématiques', 'Physique', 'Économie', 'Droit']  # adapte selon ton projet
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


def get_competences_lacunes(user_id):
    """Récupère les compétences et lacunes d'un utilisateur."""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT matiere FROM competences WHERE user_id = %s AND type = 'fort'", (user_id,))
        competences = [row['matiere'] for row in cursor.fetchall()]

        cursor.execute("SELECT matiere FROM competences WHERE user_id = %s AND type = 'faible'", (user_id,))
        lacunes = [row['matiere'] for row in cursor.fetchall()]

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

    # ── Mise à jour en BDD ───────────────────────────────────────────────────
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE users 
            SET nom = %s, prenom = %s, filiere = %s, niveau = %s, bio = %s, telephone = %s
            WHERE id = %s
        """, (nom, prenom, filiere, niveau, bio, telephone, user_id))

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