import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room  # <-- Ajout pour le chat
from routes.auth import auth_bp
from routes.messages import messages_bp  # <-- Ton Blueprint de messages
from dotenv import load_dotenv
from config.database import get_db_connection  # <-- Ta connexion MySQL
import pymysql

# 1. Chargement obligatoire des variables du fichier .env
load_dotenv()

app = Flask(__name__)

# 2. Configuration Sécurité
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
if not app.config['SECRET_KEY']:
    raise ValueError("CRITICAL ERROR : FLASK_SECRET_KEY n'est pas configuré dans ton fichier .env !")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# 3. Activation de CORS et de SocketIO pour le chat
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# 4. Enregistrement des Blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(messages_bp, url_prefix="/api")  # <-- Ajout des routes messages

# --- Routes et Gestionnaires d'erreurs ---
@app.route("/")
def home():
    return jsonify({"message": "API Flask MentorLink opérationnelle"}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route introuvable"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erreur interne du serveur"}), 500

# ─── SYSTÈME DE MESSAGERIE EN TEMPS RÉEL (COMPATIBLE MYSQL) ───
@socketio.on("rejoindre_conversation")
def rejoindre(data):
    join_room(str(data["conversation_id"]))

@socketio.on("envoyer_message")
def envoyer(data):
    connexion = None
    curseur = None
    try:
        connexion = get_db_connection()
        curseur = connexion.cursor(pymysql.cursors.DictCursor)
        
        # Requête d'insertion MySQL standard
        requete = """
            INSERT INTO messages (conversation_id, expediteur_id, contenu) 
            VALUES (%s, %s, %s)
        """
        curseur.execute(requete, (data["conversation_id"], data["expediteur_id"], data["contenu"]))
        connexion.commit()
        
        message_id = curseur.lastrowid  # Récupération de l'ID inséré (Spécifique MySQL)
        
        emit("nouveau_message", {
            "id": message_id,
            "expediteur_id": data["expediteur_id"],  
            "expediteur_nom": data["expediteur_nom"],
            "contenu": data["contenu"]
        }, room=str(data["conversation_id"]))

    except Exception as e:
        if connexion:
            connexion.rollback()
        emit("erreur", {"message": str(e)})
    finally:
        if curseur:
            curseur.close()
        if connexion:
            connexion.close()

if __name__ == "__main__":
    port_serveur = int(os.getenv("PORT", 5000))
    print(f"[*] Serveur MentorLink avec WebSockets démarré !")
    # On utilise socketio.run au lieu de app.run pour activer le mode temps réel
    socketio.run(app, host="0.0.0.0", port=port_serveur, debug=True)