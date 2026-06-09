from flask import Blueprint, jsonify, request
# Importation des fonctions de base de données depuis ton modèle
from models.message import obtenir_conversation, sauvegarder_message 

messages_bp = Blueprint('messages', __name__)

@messages_bp.route("/conversations/<int:conversation_id>", methods=["GET"])
def recuperer_historique(conversation_id):
    """
    Route API qui permet au frontend de charger tous les anciens 
    messages d'une discussion au chargement de la page.
    """
    try:
        historique = obtenir_conversation(conversation_id)
        return jsonify(historique), 200
    except Exception as e:
        print(f"[ERROR] Impossible de recuperer l'historique : {str(e)}")
        return jsonify({"error": "Erreur lors de la recuperation des messages"}), 500