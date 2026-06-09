# =====================================================================
# PROJET MENTORLINK (PIL1_2526_13)
# Fichier : backend/routes/matching.py
# Rôle : Algorithme de matching + gestion des offres et demandes
# =====================================================================

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Offer, Request as MentorRequest

matching_bp = Blueprint('matching', __name__)


# ─────────────────────────────────────────────
# ALGORITHME DE SCORING (barème officiel)
# ─────────────────────────────────────────────

def compute_score(user_a: dict, user_b: dict) -> int:
    """
    Calcule le score de compatibilité entre deux profils.
    Score max : 100 points
      - Matières / compétences communes : +40 pts
      - Disponibilités horaires compatibles : +30 pts
      - Proximité de filière : +20 pts
      - Proximité de niveau d'étude : +10 pts
    """
    score = 0

    # ── 1. Compétences communes (40 pts) ──────────────────────────
    skills_a = set(user_a.get("skills", []))
    skills_b = set(user_b.get("skills", []))
    total_skills = skills_a | skills_b
    if total_skills:
        ratio = len(skills_a & skills_b) / len(total_skills)
        score += int(ratio * 40)

    # ── 2. Disponibilités compatibles (30 pts) ────────────────────
    avail_a = set(user_a.get("availabilities", []))
    avail_b = set(user_b.get("availabilities", []))
    total_avail = avail_a | avail_b
    if total_avail:
        ratio = len(avail_a & avail_b) / len(total_avail)
        score += int(ratio * 30)

    # ── 3. Proximité de filière (20 pts) ──────────────────────────
    FILIERES = ["IA", "IM", "GL", "SE_IOT", "SI"]
    filiere_a = user_a.get("filiere", "")
    filiere_b = user_b.get("filiere", "")
    if filiere_a in FILIERES and filiere_b in FILIERES:
        dist = abs(FILIERES.index(filiere_a) - FILIERES.index(filiere_b))
        if dist == 0:
            score += 20
        elif dist == 1:
            score += 10
        elif dist == 2:
            score += 5

    # ── 4. Proximité de niveau (10 pts) ───────────────────────────
    try:
        niveau_a = int(user_a.get("niveau", 0))
        niveau_b = int(user_b.get("niveau", 0))
        diff = abs(niveau_a - niveau_b)
        if diff == 0:
            score += 10
        elif diff == 1:
            score += 7
        elif diff == 2:
            score += 3
    except (ValueError, TypeError):
        pass

    return min(score, 100)


def build_user_profile(user: User) -> dict:
    """Construit un dictionnaire de profil à partir de l'ORM."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "filiere": user.filiere or "",
        "niveau": user.niveau or 0,
        "skills": [us.skill.name for us in user.user_skills],
        "availabilities": [a.slot for a in user.availabilities],
        "bio": user.bio or "",
        "role": user.role,
    }


# ─────────────────────────────────────────────
# ROUTES OFFRES
# ─────────────────────────────────────────────

@matching_bp.route("/offers", methods=["POST"])
@jwt_required()
def create_offer():
    """Créer une offre de mentorat."""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Corps JSON manquant"}), 400

    for field in ["title", "description", "skills_offered"]:
        if field not in data:
            return jsonify({"error": f"Champ manquant : {field}"}), 400

    offer = Offer(
        user_id=current_user_id,
        title=data["title"],
        description=data["description"],
        skills_offered=",".join(data["skills_offered"]),
        status="active"
    )
    db.session.add(offer)
    db.session.commit()
    return jsonify({"message": "Offre créée", "offer_id": offer.id}), 201


@matching_bp.route("/offers", methods=["GET"])
@jwt_required()
def list_offers():
    """Lister toutes les offres actives."""
    offers = Offer.query.filter_by(status="active").all()
    return jsonify([{
        "id": o.id,
        "user_id": o.user_id,
        "username": o.author.username,
        "filiere": o.author.filiere,
        "niveau": o.author.niveau,
        "title": o.title,
        "description": o.description,
        "skills_offered": o.skills_offered.split(","),
    } for o in offers]), 200


# ─────────────────────────────────────────────
# ROUTES DEMANDES
# ─────────────────────────────────────────────

@matching_bp.route("/requests", methods=["POST"])
@jwt_required()
def create_request():
    """Créer une demande de mentorat."""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Corps JSON manquant"}), 400

    for field in ["title", "description", "skills_needed"]:
        if field not in data:
            return jsonify({"error": f"Champ manquant : {field}"}), 400

    req = MentorRequest(
        user_id=current_user_id,
        title=data["title"],
        description=data["description"],
        skills_needed=",".join(data["skills_needed"]),
        status="active"
    )
    db.session.add(req)
    db.session.commit()
    return jsonify({"message": "Demande créée", "request_id": req.id}), 201


@matching_bp.route("/requests", methods=["GET"])
@jwt_required()
def list_requests():
    """Lister toutes les demandes actives."""
    reqs = MentorRequest.query.filter_by(status="active").all()
    return jsonify([{
        "id": r.id,
        "user_id": r.user_id,
        "username": r.requester.username,
        "filiere": r.requester.filiere,
        "niveau": r.requester.niveau,
        "title": r.title,
        "description": r.description,
        "skills_needed": r.skills_needed.split(","),
    } for r in reqs]), 200


# ─────────────────────────────────────────────
# ROUTE PRINCIPALE : GET /matching/<user_id>
# ─────────────────────────────────────────────

@matching_bp.route("/matching/<int:user_id>", methods=["GET"])
@jwt_required()
def get_matches(user_id):
    """Retourne la liste des utilisateurs compatibles triée par score décroissant."""
    current_user = db.session.get(User, user_id)
    if not current_user:
        return jsonify({"error": "Utilisateur introuvable"}), 404

    current_profile = build_user_profile(current_user)
    candidates = User.query.filter(User.id != user_id).all()

    results = []
    for candidate in candidates:
        candidate_profile = build_user_profile(candidate)
        score = compute_score(current_profile, candidate_profile)
        if score > 0:
            results.append({**candidate_profile, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)

    return jsonify({
        "user_id": user_id,
        "total": len(results),
        "matches": results
    }), 200


# ─────────────────────────────────────────────
# TEST STANDALONE
# ─────────────────────────────────────────────

def test_scoring():
    alice = {
        "filiere": "IA", "niveau": 2,
        "skills": ["Python", "Machine Learning", "SQL", "Docker"],
        "availabilities": ["lundi_matin", "mercredi_soir", "vendredi_matin"],
    }
    bob = {
        "filiere": "IA", "niveau": 3,
        "skills": ["Python", "Deep Learning", "SQL", "Linux"],
        "availabilities": ["lundi_matin", "jeudi_soir", "vendredi_matin"],
    }
    carol = {
        "filiere": "GL", "niveau": 1,
        "skills": ["Java", "Git", "SQL"],
        "availabilities": ["mardi_matin", "jeudi_matin"],
    }

    print("=== Test Algorithme de Scoring ===")
    print(f"Alice ↔ Bob : {compute_score(alice, bob)}/100")
    print(f"Alice ↔ Carol : {compute_score(alice, carol)}/100")
    print(f"Bob ↔ Carol : {compute_score(bob, carol)}/100")


if __name__ == "__main__":
    test_scoring()