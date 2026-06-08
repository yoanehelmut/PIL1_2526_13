import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import pymysql # Importation nécessaire pour spécifier le type de curseur
        # CORRECTION : On force l'utilisation du DictCursor pour être en accord avec config/database.py
        curseur = connexion.cursor(pymysql.cursors.DictCursor)
       
        # Requête d'insertion standard
        requete = """
            INSERT INTO messages (conversation_id, expediteur_id, contenu)
            VALUES (%s, %s, %s)
        """
        curseur.execute(requete, (data["conversation_id"], data["expediteur_id"], data["contenu"]))
        connexion.commit()
       
        message_id = curseur.lastrowid
       
        # OPTIMISATION : On récupère le timestamp créé automatiquement par MySQL pour le renvoyer au front

        curseur.execute("SELECT timestamp FROM messages WHERE id = %s", (message_id,))
        resultat = curseur.fetchone()
        timestamp_str = str(resultat["timestamp"]) if resultat else ""
       
        # Diffusion instantanée du message à tous les membres du salon
        emit("nouveau_message", {
            "id": message_id,
            "conversation_id": data["conversation_id"],
            "expediteur_id": data["expediteur_id"],  
            "expediteur_nom": data["expediteur_nom"],
            "contenu": data["contenu"],
            "timestamp": timestamp_str
        }, room=str(data["conversation_id"]))

    except Exception as e:
        if connexion:
            connexion.rollback()
        emit("erreur", {"message": f"Erreur de transmission : {str(e)}"})
    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()


# 7. Démarrage du serveur
if __name__ == "__main__":
    port_serveur = int(os.getenv("PORT", 5000))
    print(f"[*] Serveur MentorLink démarré sur le port {port_serveur} !")
    socketio.run(app, host="0.0.0.0", port=port_serveur, debug=True)


Le lun. 8 juin 2026 à 19:04, neriad <arodagbodoyetin@gmail.com> a écrit :
# =====================================================================
# PROJET MENTORLINK (PIL1_2526_13)
# Fichier : backend/app.py
# Rôle : Point d'entrée principal (Serveur Flask + WebSockets SocketIO)
# =====================================================================

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

# 1. Chargement des variables d'environnement (.env)
load_dotenv()

app = Flask(__name__)

# 2. Configuration Sécurité & Sessions
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", os.getenv("SECRET_KEY", "mentorlink2026"))

# Outil de hachage de mots de passe pour l'authentification
bcrypt = Bcrypt(app)

# 3. Activation de CORS et de SocketIO pour le chat en temps réel
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# 4. Importation de notre connecteur de base de données validé
from config.database import get_db_connection

# 5. Importation et Enregistrement des Blueprints de l'API
from routes.auth import auth_bp
from routes.messages import messages_bp

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(messages_bp, url_prefix="/api")

# 6. Routes de base et gestionnaires d'erreurs (REST JSON)
@app.route("/")
def home():
    return jsonify({"message": "API Flask MentorLink opérationnelle (Groupe 13)"}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route introuvable"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erreur interne du serveur"}), 500


# ─── SYSTÈME DE MESSAGERIE EN TEMPS RÉEL (SOCKETIO) ───

@socketio.on("rejoindre_conversation")
def rejoindre(data):
    """Place l'utilisateur dans un salon de discussion privé."""
    join_room(str(data["conversation_id"]))

@socketio.on("envoyer_message")
def envoyer(data):
    """Reçoit un message du frontend, l'enregistre en BDD et le diffuse au salon."""
    connexion = None
    curseur = None
    try:
        connexion = get_db_connection()
        # On force l'utilisation du DictCursor pour conserver une cohérence structurelle
        import pymysql
        curseur = connexion.cursor(pymysql.cursors.DictCursor)
       
        # Requête d'insertion standard alignée avec database.sql
        requete = """
            INSERT INTO messages (conversation_id, expediteur_id, contenu)
            VALUES (%s, %s, %s)
        """
        curseur.execute(requete, (data["conversation_id"], data["expediteur_id"], data["contenu"]))
        connexion.commit()
       
        message_id = curseur.lastrowid
       
        # Récupération optionnelle du timestamp généré par MySQL pour l'affichage frontend
        curseur.execute("SELECT timestamp FROM messages WHERE id = %s", (message_id,))
        resultat = curseur.fetchone()
        timestamp_str = str(resultat["timestamp"]) if resultat else ""
       
        # Diffusion instantanée du message à tous les membres du salon
        emit("nouveau_message", {
            "id": message_id,
            "conversation_id": data["conversation_id"],
            "expediteur_id": data["expediteur_id"],  
            "expediteur_nom": data["expediteur_nom"],
            "contenu": data["contenu"],
            "timestamp": timestamp_str
        }, room=str(data["conversation_id"]))

    except Exception as e:
        if connexion:
            connexion.rollback()
        emit("erreur", {"message": f"Erreur de transmission : {str(e)}"})
    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()


# 7. Démarrage du serveur
if __name__ == "__main__":
    port_serveur = int(os.getenv("PORT", 5000))
    print(f"[*] Serveur MentorLink démarré sur le port {port_serveur} !")
    socketio.run(app, host="0.0.0.0", port=port_serveur, debug=True)


Le lun. 8 juin 2026 à 18:55, neriad <arodagbodoyetin@gmail.com> a écrit :
# =====================================================================
# PROJET MENTORLINK (PIL1_2526_13)
# Fichier : backend/app.py
# Rôle : Point d'entrée principal (Serveur Flask + WebSockets SocketIO)
# =====================================================================

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

# 1. Chargement des variables d'environnement (.env)
load_dotenv()

app = Flask(__name__)

# 2. Configuration Sécurité & Sessions
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", os.getenv("SECRET_KEY", "mentorlink2026"))

# Outil de hachage de mots de passe pour l'authentification
bcrypt = Bcrypt(app)

# 3. Activation de CORS et de SocketIO pour le chat en temps réel
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# 4. Importation de notre connecteur de base de données validé
from config.database import get_db_connection

# 5. Importation et Enregistrement des Blueprints de l'API
from routes.auth import auth_bp
from routes.messages import messages_bp

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(messages_bp, url_prefix="/api")

# 6. Routes de base et gestionnaires d'erreurs (REST JSON)
@app.route("/")
def home():
    return jsonify({"message": "API Flask MentorLink opérationnelle (Groupe 13)"}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route introuvable"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erreur interne du serveur"}), 500


# ─── SYSTÈME DE MESSAGERIE EN TEMPS RÉEL (SOCKETIO) ───

@socketio.on("rejoindre_conversation")
def rejoindre(data):
    """Place l'utilisateur dans un salon de discussion privé."""
    join_room(str(data["conversation_id"]))

@socketio.on("envoyer_message")
def envoyer(data):
    """Reçoit un message du frontend, l'enregistre en BDD et le diffuse au salon."""
    connexion = None
    curseur = None
    try:
        connexion = get_db_connection()
        # On force l'utilisation du DictCursor pour conserver une cohérence structurelle
        import pymysql
        curseur = connexion.cursor(pymysql.cursors.DictCursor)
       
        # Requête d'insertion standard alignée avec database.sql
        requete = """
            INSERT INTO messages (conversation_id, expediteur_id, contenu)
            VALUES (%s, %s, %s)
        """
        curseur.execute(requete, (data["conversation_id"], data["expediteur_id"], data["contenu"]))
        connexion.commit()
       
        message_id = curseur.lastrowid
       
        # Récupération optionnelle du timestamp généré par MySQL pour l'affichage frontend
        curseur.execute("SELECT timestamp FROM messages WHERE id = %s", (message_id,))
        resultat = curseur.fetchone()
        timestamp_str = str(resultat["timestamp"]) if resultat else ""
       
        # Diffusion instantanée du message à tous les membres du salon
        emit("nouveau_message", {
            "id": message_id,
            "conversation_id": data["conversation_id"],
            "expediteur_id": data["expediteur_id"],  
            "expediteur_nom": data["expediteur_nom"],
            "contenu": data["contenu"],
            "timestamp": timestamp_str
        }, room=str(data["conversation_id"]))

    except Exception as e:
        if connexion:
            connexion.rollback()
        emit("erreur", {"message": f"Erreur de transmission : {str(e)}"})
    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()


# 7. Démarrage du serveur
if __name__ == "__main__":
    port_serveur = int(os.getenv("PORT", 5000))
    print(f"[*] Serveur MentorLink démarré sur le port {port_serveur} !")
    socketio.run(app, host="0.0.0.0", port=port_serveur, debug=True)


Le lun. 8 juin 2026 à 18:39, neriad <arodagbodoyetin@gmail.com> a écrit :
# =====================================================================
# PROJET MENTORLINK (PIL1_2526_13)
# Fichier : backend/app.py
# Rôle : Point d'entrée principal épuré (Serveur Flask + WebSockets SocketIO)
# =====================================================================

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

# 1. Chargement des variables d'environnement (.env)
load_dotenv()

app = Flask(__name__)

# 2. Configuration Sécurité & Sessions
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", os.getenv("SECRET_KEY", "mentorlink2026"))

# Outil de hachage de mots de passe pour l'authentification
bcrypt = Bcrypt(app)

# 3. Activation de CORS et de SocketIO pour le chat en temps réel
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# 4. Importation de notre connecteur de base de données validé
from config.database import get_db_connection

# 5. Importation et Enregistrement des Blueprints de l'API
from routes.auth import auth_bp
from routes.messages import messages_bp

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(messages_bp, url_prefix="/api")

# 6. Routes de base et gestionnaires d'erreurs (REST JSON)
@app.route("/")
def home():
    return jsonify({"message": "API Flask MentorLink opérationnelle (Groupe 13)"}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route introuvable"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erreur interne du serveur"}), 500


# ─── SYSTÈME DE MESSAGERIE EN TEMPS RÉEL (SOCKETIO) ───

@socketio.on("rejoindre_conversation")
def rejoindre(data):
    """Place l'utilisateur dans un salon de discussion privé."""
    join_room(str(data["conversation_id"]))

@socketio.on("envoyer_message")
def envoyer(data):
    """Reçoit un message du frontend, l'enregistre en BDD et le diffuse au salon."""
    connexion = None
    curseur = None
    try:
        connexion = get_db_connection()
        curseur = connexion.cursor()
       
        # Requête d'insertion standard
        requete = """
            INSERT INTO messages (conversation_id, expediteur_id, contenu)
            VALUES (%s, %s, %s)
        """
        curseur.execute(requete, (data["conversation_id"], data["expediteur_id"], data["contenu"]))
        connexion.commit()
       
        message_id = curseur.lastrowid
       
        # Diffusion instantanée du message à tous les membres du salon
        emit("nouveau_message", {
            "id": message_id,
            "conversation_id": data["conversation_id"],
            "expediteur_id": data["expediteur_id"],  
            "expediteur_nom": data["expediteur_nom"],
            "contenu": data["contenu"]
        }, room=str(data["conversation_id"]))

    except Exception as e:
        if connexion:
            connexion.rollback()
        emit("erreur", {"message": f"Erreur de transmission : {str(e)}"})
    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()


# 7. Démarrage du serveur
if __name__ == "__main__":
    port_serveur = int(os.getenv("PORT", 5000))
    print(f"[*] Serveur MentorLink démarré sur le port {port_serveur} !")
    socketio.run(app, host="0.0.0.0", port=port_serveur, debug=True)

Le lun. 8 juin 2026 à 18:11, Raphael Dave <raphdave119@gmail.com> a écrit :
from flask import Flask, render_template, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from flask_bcrypt import Bcrypt
import psycopg2, os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "mentorlink2026")
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "mentorlink"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        port=os.getenv("DB_PORT", "5432")
    )

from routes.auth import auth_bp
from routes.messages import messages_bp
app.register_blueprint(auth_bp)
app.register_blueprint(messages_bp)

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth.login"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html", user=session)

@socketio.on("rejoindre_conversation")
def rejoindre(data):
    join_room(str(data["conversation_id"]))

@socketio.on("envoyer_message")
def envoyer(data):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (conversation_id, expediteur_id, contenu) VALUES (%s,%s,%s) RETURNING id, date_envoi",
            (data["conversation_id"], data["expediteur_id"], data["contenu"])
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        emit("nouveau_message", {
            "id": row[0],
            "expediteur_id": data["expediteur_id"],  
            "expediteur_nom": data["expediteur_nom"],
            "contenu": data["contenu"],
            "date_envoi": str(row[1]) 
        }, room=str(data["conversation_id"]))
    except Exception as e:
        emit("erreur", {"message": str(e)})

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
=======
from flask import Flask
from flask_cors import CORS
from config.config import Config
from routes.auth import auth_bp

app = Flask(__name__)

# config
app.config.from_object(Config)

# blueprints
app.register_blueprint (auth_bp, url_prefix="/auth")


@app.route("/")
def home():
    return {"message": "API Flask opérationnelle"}
@app.errorhandler(404)
def not_found(e):
    return {"error": "Route introuvable"}, 404

@app.errorhandler(500)
def server_error(e):
    return {"error":"Erreur serveur"}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
>>>>>>> d74c97c5b1ce488caa2b1f8a8a1fdbc44c6aeafb

