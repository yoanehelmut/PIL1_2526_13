import os

class Config:
    # Sécurité Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key")

    # Base de données
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "mentorlink_db")

    # Session sécurité
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # mettre True en production

    # Debug
    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
