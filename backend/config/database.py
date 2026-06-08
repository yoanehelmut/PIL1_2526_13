
import os
import pymysql
from urllib.parse import urlparse
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

def get_db_connection():
    """
    Récupère l'URL de la base de données dans le .env, 
    la découpe et retourne une connexion active vers MySQL.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("CRITICAL ERROR : DATABASE_URL n'est pas configuré dans ton fichier .env !")
    
    # Découpe l'URL proprement (ex: mysql://user:pass@host:port/db)
    url_decoupee = urlparse(db_url)
    
    mot_de_passe = url_decoupee.password if url_decoupee.password is not None else ""
    
    return pymysql.connect(
        host=url_decoupee.hostname,
        user=url_decoupee.username,
        password=mot_de_passe,
        port=url_decoupee.port or 3306,
        database=url_decoupee.path.lstrip('/'),
        cursorclass=pymysql.cursors.DictCursor,  # Récupère les lignes SQL sous forme de dictionnaires
        autocommit=False  # Permet à l'équipe de gérer manuellement les commits et rollbacks
    )