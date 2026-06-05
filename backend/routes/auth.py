import os
import re
import logging
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import pymysql
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# ─────────────────────────────────────────────
# Configuration Flask
# ─────────────────────────────────────────────

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "La variable d'environnement SECRET_KEY doit être définie."
    )

app.secret_key = SECRET_KEY

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get(
        "FLASK_ENV"
    ) == "production"
)

logging.basicConfig(level=logging.INFO)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"


# ─────────────────────────────────────────────
# Base de données
# ─────────────────────────────────────────────

def get_db_connection():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "mentorlink_db"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )


# ─────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────

def is_valid_email(email):
    return re.match(EMAIL_REGEX, email)


def is_valid_phone(phone):
    return phone.isdigit() and len(phone) >= 8


# ─────────────────────────────────────────────
# Décorateur connexion
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash(
                "Veuillez vous connecter.",
                "warning"
            )
            return redirect(
                url_for(
                    "connexion",
                    next=request.url
                )
            )

        return f(*args, **kwargs)

    return decorated_function


# ─────────────────────────────────────────────
# Accueil
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("connexion"))


# ─────────────────────────────────────────────
# Inscription
# ─────────────────────────────────────────────

@app.route("/inscription", methods=["GET", "POST"])
def inscription():

    if request.method == "POST":

        nom = request.form.get("nom", "").strip()
        prenom = request.form.get("prenom", "").strip()
        telephone = request.form.get("telephone", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("mot_de_passe", "")
        filiere = request.form.get("filiere", "").strip()
        niveau = request.form.get("niveau_etudes", "").strip()

        if not all([
            nom,
            prenom,
            telephone,
            email,
            password,
            filiere,
            niveau
        ]):
            flash(
                "Tous les champs sont obligatoires.",
                "danger"
            )
            return redirect(url_for("inscription"))

        if not is_valid_email(email):
            flash(
                "Adresse email invalide.",
                "danger"
            )
            return redirect(url_for("inscription"))

        if not is_valid_phone(telephone):
            flash(
                "Numéro de téléphone invalide.",
                "danger"
            )
            return redirect(url_for("inscription"))

        hashed_password = generate_password_hash(password)

        conn = None

        try:
            conn = get_db_connection()

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT id
                    FROM utilisateurs
                    WHERE email = %s
                    OR telephone = %s
                    """,
                    (email, telephone)
                )

                if cursor.fetchone():
                    flash(
                        "Email ou téléphone déjà utilisé.",
                        "danger"
                    )
                    return redirect(url_for("inscription"))

                cursor.execute(
                    """
                    INSERT INTO utilisateurs
                    (
                        nom,
                        prenom,
                        telephone,
                        email,
                        mot_de_passe,
                        filiere,
                        niveau_etudes
                    )
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        nom,
                        prenom,
                        telephone,
                        email,
                        hashed_password,
                        filiere,
                        niveau
                    )
                )

                conn.commit()

            flash(
                "Inscription réussie.",
                "success"
            )

            return redirect(url_for("connexion"))

        except Exception as e:

            if conn:
                conn.rollback()

            app.logger.exception(e)

            flash(
                "Erreur lors de l'inscription.",
                "danger"
            )

        finally:

            if conn:
                conn.close()

    return render_template("inscription.html")


# ─────────────────────────────────────────────
# Connexion
# ─────────────────────────────────────────────

@app.route("/connexion", methods=["GET", "POST"])
def connexion():

    if request.method == "POST":

        identifiant = request.form.get(
            "identifiant",
            ""
        ).strip()

        password = request.form.get(
            "mot_de_passe",
            ""
        )

        if not identifiant or not password:
            flash(
                "Veuillez remplir tous les champs.",
                "danger"
            )
            return redirect(url_for("connexion"))

        if "@" in identifiant:
            identifiant = identifiant.lower()

        conn = None

        try:

            conn = get_db_connection()

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT *
                    FROM utilisateurs
                    WHERE email = %s
                    OR telephone = %s
                    """,
                    (identifiant, identifiant)
                )

                user = cursor.fetchone()

            if user and check_password_hash(
                user["mot_de_passe"],
                password
            ):

                session["user_id"] = user["id"]
                session["user_nom"] = (
                    f"{user['prenom']} {user['nom']}"
                )

                flash(
                    f"Bienvenue {user['prenom']} !",
                    "success"
                )

                next_page = request.args.get("next")

                return redirect(
                    next_page or url_for("profil")
                )

            flash(
                "Identifiant ou mot de passe incorrect.",
                "danger"
            )

        except Exception as e:

            app.logger.exception(e)

            flash(
                "Erreur lors de la connexion.",
                "danger"
            )

        finally:

            if conn:
                conn.close()

    return render_template("connexion.html")


# ─────────────────────────────────────────────
# Profil
# ─────────────────────────────────────────────

@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():

    user_id = session["user_id"]

    conn = None

    try:

        conn = get_db_connection()

        with conn.cursor() as cursor:

            if request.method == "POST":

                cursor.execute(
                    """
                    UPDATE utilisateurs
                    SET
                        points_forts=%s,
                        points_faibles=%s,
                        disponibilites=%s,
                        bio=%s
                    WHERE id=%s
                    """,
                    (
                        request.form.get(
                            "points_forts",
                            ""
                        ).strip(),

                        request.form.get(
                            "points_faibles",
                            ""
                        ).strip(),

                        request.form.get(
                            "disponibilites",
                            ""
                        ).strip(),

                        request.form.get(
                            "bio",
                            ""
                        ).strip(),

                        user_id
                    )
                )

                conn.commit()

                flash(
                    "Profil mis à jour.",
                    "success"
                )

                return redirect(
                    url_for("profil")
                )

            cursor.execute(
                """
                SELECT *
                FROM utilisateurs
                WHERE id = %s
                """,
                (user_id,)
            )

            user = cursor.fetchone()

        if not user:

            session.clear()

            flash(
                "Utilisateur introuvable.",
                "danger"
            )

            return redirect(
                url_for("connexion")
            )

        return render_template(
            "profil.html",
            user=user
        )

    except Exception as e:

        app.logger.exception(e)

        flash(
            "Une erreur est survenue.",
            "danger"
        )

        return redirect(
            url_for("connexion")
        )

    finally:

        if conn:
            conn.close()


# ─────────────────────────────────────────────
# Déconnexion
# ─────────────────────────────────────────────

@app.route(
    "/deconnexion",
    methods=["POST"]
)
@login_required
def deconnexion():

    session.clear()

    flash(
        "Vous avez été déconnecté.",
        "info"
    )

    return redirect(
        url_for("connexion")
    )


# ─────────────────────────────────────────────
# Lancement
# ─────────────────────────────────────────────

if __name__ == "__main__":

    debug_mode = (
        os.environ.get(
            "FLASK_DEBUG",
            "false"
        ).lower() == "true"
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=debug_mode
    )