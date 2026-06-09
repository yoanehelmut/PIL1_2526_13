import os
import pymysql
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
CORS(app, supports_credentials=True, resources={r"/": {"origins": ""}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# 4. Importation de notre connecteur de base de données validé
from config.database import get_db_connection

# 5. Importation et Enregistrement des Blueprints de l'API
from routes.auth import auth_bp
from models.message import messages_bp
from routes.matching import matching_bp  # AJOUT : Importation du Blueprint matching

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(messages_bp, url_prefix="/api")
app.register_blueprint(matching_bp, url_prefix="/api")  # AJOUT : Enregistrement du Blueprint matching

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
        # On force l'utilisation du DictCursor pour être en accord avec config/database.py
        curseur = connexion.cursor(pymysql.cursors.DictCursor)
        
        # Requête d'insertion standard alignée avec database.sql
        requete = """
            INSERT INTO messages (conversation_id, expediteur_id, contenu)
            VALUES (%s, %s, %s)
        """
        curseur.execute(requete, (data["conversation_id"], data["expediteur_id"], data["contenu"]))
        connexion.commit()
        
        message_id = curseur.lastrowid
        
        # Optimisation : Récupération du timestamp créé automatiquement par MySQL pour le renvoyer au front
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