from flask import Flask
from config.config import Config
from routes.auth import auth_bp

app = Flask(__name__)

# config
app.config.from_object(Config)

# blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")


@app.route("/")
def home():
    return {"message": "API Flask opérationnelle"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
