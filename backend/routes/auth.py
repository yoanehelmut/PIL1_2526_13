import re
import logging
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import get_db_connection

auth_bp = Blueprint("auth", __name__)

logger = logging.getLogger(__name__)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"  # Fix: TLD min 2 caractères
ALLOWED_ROLES = {"student", "teacher"}


# 🔹 REGISTER
@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON invalide"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "student")

    # Validation des champs obligatoires
    if not name or not email or not password:
        return jsonify({"message": "Champs manquants"}), 400

    # Fix: longueur minimale du mot de passe
    if len(password) < 8:
        return jsonify({"message": "Mot de passe trop court (8 caractères min)"}), 400

    if not re.match(EMAIL_REGEX, email):
        return jsonify({"message": "Email invalide"}), 400

    # Fix: whitelist des rôles — empêche l'auto-attribution de "admin"
    if role not in ALLOWED_ROLES:
        role = "student"

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            return jsonify({"message": "Email déjà utilisé"}), 409

        hashed = generate_password_hash(password)

        cur.execute("""
            INSERT INTO users(name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
        """, (name, email, hashed, role))

        conn.commit()

        return jsonify({"message": "Utilisateur créé"}), 201

    except Exception as e:
        conn.rollback()
        logger.error("Erreur register: %s", e)  # Fix: log de l'erreur
        return jsonify({"message": "Erreur serveur"}), 500

    finally:
        cur.close()
        conn.close()


# 🔹 LOGIN
@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON invalide"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Fix: validation des champs manquants
    if not email or not password:
        return jsonify({"message": "Champs manquants"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Fix: try/except pour gérer les erreurs DB proprement
    try:
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"message": "Identifiants incorrects"}), 401

        # Fix: ajout du role en session
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_role"] = user["role"]

        return jsonify({"message": "Connexion OK"}), 200

    except Exception as e:
        logger.error("Erreur login: %s", e)
        return jsonify({"message": "Erreur serveur"}), 500

    finally:
        cur.close()
        conn.close()


# 🔹 ME
@auth_bp.route("/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"message": "Non connecté"}), 401

    # Fix: on retourne aussi le role
    return jsonify({
        "id": session["user_id"],
        "name": session["user_name"],
        "role": session["user_role"],
    })


# 🔹 LOGOUT
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Déconnecté"})


