<<<<<<< HEAD
import re
import logging
import pymysql
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import get_db_connection

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"

# CORRIGÉ : Alignement strict sur l'ENUM de ta table MySQL
ALLOWED_ROLES = {"mentor", "etudiant"}

# 🔹 REGISTER
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON invalide"}), 400

    # CORRIGÉ : Utilisation des colonnes de ta table users
    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "etudiant").strip().lower()
    filiere = data.get("filiere", None)
    niveau = data.get("niveau", None)

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
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            return jsonify({"message": "Email déjà utilisé"}), 409

        hashed = generate_password_hash(password)

        # CORRIGÉ : Requête SQL calquée sur ta structure réelle
        cur.execute("""
            INSERT INTO users(nom, prenom, email, mot_de_passe_hash, role, filiere, niveau)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nom, prenom, email, hashed, role, filiere, niveau))

        conn.commit()
        return jsonify({"message": "Utilisateur créé"}), 201

    except Exception as e:
        conn.rollback()
        logger.error("Erreur register: %s", e)
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

    if not email or not password:
        return jsonify({"message": "Champs manquants"}), 400

    conn = get_db_connection()
    # CORRIGÉ : On force le DictCursor pour pouvoir manipuler les clés textuelles
    cur = conn.cursor(pymysql.cursors.DictCursor)

    try:
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        # CORRIGÉ : Vérification avec 'mot_de_passe_hash'
        if not user or not check_password_hash(user["mot_de_passe_hash"], password):
            return jsonify({"message": "Identifiants incorrects"}), 401

        # CORRIGÉ : Données de session synchronisées
        session["user_id"] = user["id"]
        session["user_nom"] = user["nom"]
        session["user_prenom"] = user["prenom"]
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

    return jsonify({
        "id": session["user_id"],
        "nom": session["user_nom"],
        "prenom": session["user_prenom"],
        "role": session["user_role"],
    })


# 🔹 LOGOUT
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
<<<<<<< HEAD
    return jsonify({"message": "Déconnecté"})
=======
    return jsonify({"message": "Déconnecté"})


=======
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import *
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    nom = data["nom"]
    E_mail = data["E-mail"]
    Mot_de_passe = data["Mot_de_passe"]
    Rôle = data["Rôle"]
    if not nom or E_mail or Mot_de_passe or Rôle:
        return jsonify({ "error": "Tous les champs sont obligatoires"})
    user_exist = user.query.filter_by(E_mail=E_mail).first()
    if user_exist:
        return jsonify({"error": "Cet e-mail existe déjà"}), 409
    if len (Mot_de_passe) < 6:
        return jsonify({"error": "Mot de passe trop court"}), 400
    hashed_password = generate_password_hash(password)
    new_user = User(E_mail=E_mail, password=hashed_password)
    
>>>>>>> f886a4d (feat: ajout offre_demande et modification auth)
>>>>>>> c84f7e96a267d9cf97a6c3131606b843eace6625
