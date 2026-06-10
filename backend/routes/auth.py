import re
import logging
import pymysql
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import get_db_connection

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
ALLOWED_ROLES = {"mentor", "etudiant"}


# 🔹 REGISTER
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON invalide"}), 400

    # Champs de base
    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "etudiant").strip().lower()
    filiere = data.get("filiere", None)
    niveau = data.get("niveau", None)

    # ✅ NOUVEAU : Compétences et lacunes
    competences = data.get("competences", [])
    lacunes = data.get("lacunes", [])

    if not nom or not prenom or not email or not password:
        return jsonify({"message": "Champs manquants"}), 400

    if len(password) < 8:
        return jsonify({"message": "Mot de passe trop court (8 caractères min)"}), 400

    if not re.match(EMAIL_REGEX, email):
        return jsonify({"message": "Email invalide"}), 400

    if role not in ALLOWED_ROLES:
        role = "etudiant"

    # Règle métier : un mentor n'a pas de filière ni de niveau d'études
    if role == "mentor":
        filiere = None
        niveau = None

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérifier si l'email existe déjà
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            return jsonify({"message": "Email déjà utilisé"}), 409

        # Hasher le mot de passe
        hashed = generate_password_hash(password)

        # Insérer l'utilisateur
        cur.execute("""
            INSERT INTO users(nom, prenom, email, mot_de_passe_hash, role, filiere, niveau)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nom, prenom, email, hashed, role, filiere, niveau))

        user_id = cur.lastrowid

        # ✅ Enregistrer les compétences (points forts) → type = 'mentor'
        for comp_nom in competences:
            comp_nom = comp_nom.strip()
            if not comp_nom:
                continue

            # Vérifier si la compétence existe déjà
            cur.execute("SELECT id FROM competences WHERE nom = %s", (comp_nom,))
            result = cur.fetchone()

            if result:
                comp_id = result[0]
            else:
                # Créer la compétence
                cur.execute("INSERT INTO competences (nom) VALUES (%s)", (comp_nom,))
                comp_id = cur.lastrowid

            # Lier à l'utilisateur (type = 'mentor' = compétence maîtrisée)
            cur.execute("""
                INSERT INTO user_competences (user_id, competence_id, type)
                VALUES (%s, %s, 'mentor')
                ON DUPLICATE KEY UPDATE type = 'mentor'
            """, (user_id, comp_id))

        # ✅ Enregistrer les lacunes (points faibles) → type = 'mentore'
        for lac_nom in lacunes:
            lac_nom = lac_nom.strip()
            if not lac_nom:
                continue

            # Vérifier si la compétence existe déjà
            cur.execute("SELECT id FROM competences WHERE nom = %s", (lac_nom,))
            result = cur.fetchone()

            if result:
                comp_id = result[0]
            else:
                cur.execute("INSERT INTO competences (nom) VALUES (%s)", (lac_nom,))
                comp_id = cur.lastrowid

            # Lier à l'utilisateur (type = 'mentore' = besoin d'aide)
            cur.execute("""
                INSERT INTO user_competences (user_id, competence_id, type)
                VALUES (%s, %s, 'mentore')
                ON DUPLICATE KEY UPDATE type = 'mentore'
            """, (user_id, comp_id))

        conn.commit()
        return jsonify({"message": "Utilisateur créé", "role": role}), 201

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error("Erreur register: %s", e)
        return jsonify({"message": "Erreur serveur"}), 500
    finally:
        cur.close()
        conn.close()


# 🔹 LOGIN (version améliorée : renvoie les infos utilisateur)
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON invalide"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"message": "Champs manquants"}), 400

    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    try:
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if not user or not check_password_hash(user["mot_de_passe_hash"], password):
            return jsonify({"message": "Identifiants incorrects"}), 401

        # Session
        session["user_id"] = user["id"]
        session["user_nom"] = user["nom"]
        session["user_prenom"] = user["prenom"]
        session["user_role"] = user["role"]

        # Renvoie les infos directement (évite un 2ème appel à /me)
        return jsonify({
            "message": "Connexion OK",
            "user": {
                "id": user["id"],
                "nom": user["nom"],
                "prenom": user["prenom"],
                "email": user["email"],
                "role": user["role"],
                "filiere": user.get("filiere"),
                "niveau": user.get("niveau")
            }
        }), 200

    except Exception as e:
        logger.error("Erreur login: %s", e)
        return jsonify({"message": "Erreur serveur"}), 500
    finally:
        cur.close()
        conn.close()


# 🔹 ME (version améliorée : renvoie plus d'infos)
@auth_bp.route("/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"message": "Non connecté"}), 401

    # Récupère les infos complètes depuis la BDD
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cur.execute("""
            SELECT id, nom, prenom, email, role, filiere, niveau
            FROM users 
            WHERE id = %s
        """, (session["user_id"],))
        user = cur.fetchone()
        
        if not user:
            session.clear()
            return jsonify({"message": "Utilisateur introuvable"}), 404
        
        return jsonify(user), 200
        
    except Exception as e:
        logger.error("Erreur /me: %s", e)
        return jsonify({"message": "Erreur serveur"}), 500
    finally:
        cur.close()
        conn.close()


# 🔹 LOGOUT
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Déconnecté"}), 200