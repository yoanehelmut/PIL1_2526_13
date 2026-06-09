
from flask import Blueprint, request, jsonify
from models.offre_demande import (
    create_offre_demande,
    get_all_offres_demandes,
    get_offre_demande_by_id,
    get_offres_demandes_by_user,
    delete_offre_demande
)

offer_bp = Blueprint("offer", __name__, url_prefix="/offers")
w

# =====================================================
# 1. Créer une offre ou une demande
# =====================================================
@offer_bp.route("/", methods=["POST"])
def create_offer():
    """
    POST /offers/
    Body JSON : { "user_id": 1, "type": "offre", "description": "..." }
    """
    donnees = request.get_json()

    if not donnees:
        return jsonify({"error": "Aucune donnée envoyée"}), 400

    if not all(k in donnees for k in ("user_id", "type", "description")):
        return jsonify({"error": "Champs manquants : user_id, type, description"}), 400

    if donnees["type"] not in ("offre", "demande"):
        return jsonify({"error": "Type invalide. Valeurs acceptées : 'offre' ou 'demande'"}), 400

    identifiant = create_offre_demande(
        user_id=donnees["user_id"],
        type_offre=donnees["type"],
        description=donnees["description"]
    )

    if identifiant:
        return jsonify({
            "message": "Publication créée avec succès",
            "id": identifiant
        }), 201
    else:
        return jsonify({"error": "Échec de la création"}), 500


# =====================================================
# 2. Récupérer toutes les offres/demandes
# =====================================================
@offer_bp.route("/", methods=["GET"])
def get_all_offers():
    """
    GET /offers/
    Paramètre optionnel : ?type=offre ou ?type=demande
    """
    type_filtre = request.args.get("type", None)

    # Vérification du filtre si fourni
    if type_filtre and type_filtre not in ("offre", "demande"):
        return jsonify({"error": "Filtre invalide. Valeurs acceptées : 'offre' ou 'demande'"}), 400

    liste = get_all_offres_demandes(type_filtre=type_filtre)

    return jsonify({
        "success": True,
        "total": len(liste),
        "data": liste
    }), 200


# =====================================================
# 3. Récupérer une offre/demande par ID
# =====================================================
@offer_bp.route("/<int:offre_id>", methods=["GET"])
def get_offer(offre_id):
    """
    GET /offers/<id>
    """
    offre = get_offre_demande_by_id(offre_id)

    if offre:
        return jsonify({
            "success": True,
            "data": offre
        }), 200
    else:
        return jsonify({"error": "Publication introuvable"}), 404


# =====================================================
# 4. Récupérer toutes les offres/demandes d'un user
# =====================================================
@offer_bp.route("/user/<int:user_id>", methods=["GET"])
def get_offers_by_user(user_id):
    """
    GET /offers/user/<user_id>
    """
    liste = get_offres_demandes_by_user(user_id)

    return jsonify({
        "success": True,
        "total": len(liste),
        "data": liste
    }), 200


# =====================================================
# 5. Supprimer une offre/demande
# =====================================================
@offer_bp.route("/<int:offre_id>", methods=["DELETE"])
def delete_offer(offre_id):
    """
    DELETE /offers/<id>
    Body JSON : { "user_id": 1 }
    """
    donnees = request.get_json()

    if not donnees or "user_id" not in donnees:
        return jsonify({"error": "user_id obligatoire pour supprimer"}), 400

    resultat = delete_offre_demande(offre_id, donnees["user_id"])

    if resultat:
        return jsonify({"message": "Publication supprimée avec succès"}), 200
    else:
        return jsonify({"error": "Suppression refusée : introuvable ou non autorisée"}), 403