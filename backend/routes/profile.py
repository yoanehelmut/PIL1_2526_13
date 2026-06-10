from flask import Blueprint, jsonify, session
from config.database import get_db_connection
import pymysql

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/api/profile', methods=['GET'])
def get_profile():
    """Récupérer le profil de l'utilisateur connecté"""
    if "user_id" not in session:
        return jsonify({"message": "Non connecté"}), 401
    
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Juste les infos de base de l'utilisateur
        cur.execute("""
            SELECT id, nom, prenom, email, role, filiere, niveau
            FROM users
            WHERE id = %s
        """, (user_id,))
        
        user = cur.fetchone()
        
        if not user:
            return jsonify({"message": "Utilisateur non trouvé"}), 404
        
        # Retourner uniquement les infos de base (pas de compétences/dispos pour l'instant)
        return jsonify({
            "id": user['id'],
            "nom": user['nom'],
            "prenom": user['prenom'],
            "email": user['email'],
            "role": user['role'],
            "filiere": user['filiere'] or '',
            "niveau": user['niveau'] or '',
            "competences": [],
            "lacunes": [],
            "disponibilites": []
        }), 200
        
    except Exception as e:
        print(f"Erreur GET profile: {e}")
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()