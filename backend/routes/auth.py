import re
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import contextmanager
from config.database import get_db_connection

# ─────────────────────────────
# Blueprint
# ─────────────────────────────
auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
ROLES_AUTORISÉS = {"student", "teacher"}
MIN_PASSWORD_LENGTH = 8
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 255


# ─────────────────────────────
# CONTEXT MANAGER DB
# ─────────────────────────────
@contextmanager
def get_db():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────
# VALIDATION
# ─────────────────────────────
def is_valid_email(email):
    return bool(re.match(EMAIL_REGEX, email))

def validate_register_data(data):
    if not isinstance(data, dict):
        return "JSON invalide: data n'est pas un objet", 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "student")

    if not name or not email or not password:
        return "Champs manquants", 400

    if len(name) > MAX_NAME_LENGTH:
        return f"Nom trop long (max {MAX_NAME_LENGTH} caractères)", 400

    if len(email) > MAX_EMAIL_LENGTH or not is_valid_email(email):
        return "Email invalide", 400

    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Mot de passe trop court (min {MIN_PASSWORD_LENGTH} caractères)", 400

    if role not in ROLES_AUTORISÉS:
        return f"Rôle invalide. Valeurs acceptées : {', '.join(ROLES_AUTORISÉS)}", 400

    return None, None


# ─────────────────────────────
# REGISTER
# ─────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get__json(force=True,silent=False)
    print("HEADERS:", request.headers)
    print("RAW:", request.data)
    print("JSON:", data)
    print("TYPE:", type(data))
    if not isinstance (data, dict):
        return jsonify({"message": "Corps de requête JSON invalide"}), 400

    error, status = validate_register_data(data)
    if error:
        return jsonify({"message": error}), status

    name     = data["name"].strip()
    email    = data["email"].strip().lower()
    password = data["password"]
    role     = data.get("role", "student")

    try:
        with get_db() as (conn, cur):
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({"message": "Email déjà utilisé"}), 409

            hashed_password = generate_password_hash(password)
            cur.execute("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
            """, (name, email, hashed_password, role))

    except Exception as e:
        return jsonify({"message": "Erreur serveur lors de l'inscription"}), 500

    return jsonify({"message": "Utilisateur créé avec succès"}), 201


# ─────────────────────────────
# LOGIN
# ─────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Corps de requête JSON invalide"}), 400

    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"message": "Champs manquants"}), 400

    try:
        with get_db() as (conn, cur):
            cur.execute("""
                SELECT id, name, email, password_hash, role
                FROM users
                WHERE email = %s
            """, (email,))
            user = cur.fetchone()

    except Exception:
        return jsonify({"message": "Erreur serveur lors de la connexion"}), 500

    # Message volontairement vague pour ne pas révéler si l'email existe
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"message": "Identifiants incorrects"}), 401

    session.clear()  # Évite la fixation de session
    session["user_id"]   = user["id"]
    session["user_name"] = user["name"]
    session["user_role"] = user["role"]

    return jsonify({
        "message": "Connexion réussie",
        "user": {
            "id":    user["id"],
            "name":  user["name"],
            "email": user["email"],
            "role":  user["role"]
        }
    }), 200


# ─────────────────────────────
# LOGOUT
# ─────────────────────────────
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Déconnexion réussie"}), 200


# ─────────────────────────────
# GET PROFILE
# ─────────────────────────────
@auth_bp.route("/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"message": "Non connecté"}), 401

    return jsonify({
        "user_id": session["user_id"],
        "name":    session["user_name"],
        "role":    session["user_role"]
    }), 200

