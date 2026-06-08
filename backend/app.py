import os
from flask import Flask, jsonify
from flask_cors import CORS
from routes.auth import auth_bp
from dotenv import load_dotenv

# 1. Chargement obligatoire des variables du fichier .env
load_dotenv()

app = Flask(__name__)

# 2. CORRECTION CONFIG : Récupération de la clé secrète directement depuis le .env
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
if not app.config['SECRET_KEY']:
    raise ValueError("CRITICAL ERROR : FLASK_SECRET_KEY n'est pas configuré dans ton fichier .env !")

# Sécurisation des cookies de session pour éviter les failles XSS et CSRF
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# 3. CORRECTION CORS : Activation essentielle pour que le Frontend puisse parler au Backend
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# 4. CORRECTION CONCORDANCE URL : Aligné sur le dossier des routes d'authentification
app.register_blueprint(auth_bp, url_prefix="/api/auth")


# --- Vos Routes et Gestionnaires d'erreurs d'origine (Nettoyés avec jsonify) ---

@app.route("/")
def home():
    return jsonify({"message": "API Flask MentorLink opérationnelle"}), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route introuvable"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erreur interne du serveur"}), 500


if __name__ == "__main__":
    # Récupère le port du .env (ou 5000 par défaut)
    port_serveur = int(os.getenv("PORT", 5000))
    
    print(f"[*] Serveur de développement MentorLink (PIL1_2526_13) démarré !")
    print(f"[*] URL locale de test : http://localhost:{port_serveur}")
    
    app.run(host="0.0.0.0", port=port_serveur, debug=True)