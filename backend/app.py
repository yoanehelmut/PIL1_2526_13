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
