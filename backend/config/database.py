import os
import pymysql
from urllib.parse import urlparse
from dotenv import load_dotenv

# Charge le fichier .env
load_dotenv()

def get_db_connection():
    # Récupère la ligne DATABASE_URL du .env
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("Erreur : DATABASE_URL n'est pas défini dans le fichier .env")
    
    # Découpe l'URL proprement
    url_decoupee = urlparse(db_url)
    
    return pymysql.connect(
        host=url_decoupee.hostname,
        user=url_decoupee.username,
        password=url_decoupee.password,
        port=url_decoupee.port or 3306,
        database=url_decoupee.path.lstrip('/'),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False  # Reste à False pour gérer les commits à la main
    )