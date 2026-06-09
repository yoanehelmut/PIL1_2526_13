# =====================================================================
# PROJET MENTORLINK (PIL1_2526_13)
# Fichier : backend/routes/matching.py
# Rôle : Algorithme de matching + gestion des offres et demandes (PyMySQL)
# =====================================================================

import pymysql
from flask import Blueprint, jsonify, request, session
from config.database import get_db_connection

matching_bp = Blueprint('matching', __name__)

# Listes officielles alignées avec profile.py
FILIERES_VALIDES = ['Informatique', 'Mathématiques', 'Physique', 'Économie', 'Droit']
NIVEAUX_VALIDES = ['L1', 'L2', 'L3', 'M1', 'M2']

# ─────────────────────────────────────────────
# ALGORITHME DE SCORING (Modifié pour PyMySQL)
# ─────────────────────────────────────────────

def compute_score(user_a: dict, user_b: dict) -> int:
    """Calcule le score de compatibilité entre deux profils.
    Score max : 100 points
    """
    score = 0

    # ── 1. Compétences / Matières communes (40 pts) ────────────────
    # Recherche les correspondances entre les compétences de l'un et les lacunes de l'autre
    skills_a = set(user_a.get("skills", []))
    skills_b = set(user_b.get("skills", []))
    total_skills = skills_a | skills_b
    if total_skills:
        ratio = len(skills_a & skills_b) / len(total_skills)
        score += int(ratio * 40)

    # ── 2. Disponibilités (30 pts) (Simulation ou à implémenter si géré en BDD) ─
    avail_a = set(user_a.get("availabilities", []))
    avail_b = set(user_b.get("availabilities", []))
    total_avail = avail_a | avail_b
    if total_avail:
        ratio = len(avail_a & avail_b) / len(total_avail)
        score += int(ratio * 30)

    # ── 3. Proximité de filière (20 pts) ──────────────────────────
    filiere_a = user_a.get("filiere", "")
    filiere_b = user_b.get("filiere", "")
    if filiere_a in FILIERES_VALIDES and filiere_b in FILIERES_VALIDES:
        dist = abs(FILIERES_VALIDES.index(filiere_a) - FILIERES_VALIDES.index(filiere_b))
        if dist == 0:
            score += 20
        elif dist == 1:
            score += 10
        elif dist == 2:
            score += 5

    # ── 4. Proximité de niveau (10 pts) ───────────────────────────
    filiere_a_niv = user_a.get("niveau", "")
    filiere_b_niv = user_b.get("niveau", "")
    if filiere_a_niv in NIVEAUX_VALIDES and filiere_b_niv in NIVEAUX_VALIDES:
        diff = abs(NIVEAUX_VALIDES.index(filiere_a_niv) - NIVEAUX_VALIDES.index(filiere_b_niv))
        if diff == 0:
            score += 10
        elif diff == 1:
            score += 7
        elif diff == 2:
            score += 3

    return min(score, 100)


def get_user_matching_profile(user_id, cursor):
    """Construit dynamiquement le profil complet pour l'algorithme."""
    cursor.execute("SELECT id, nom, prenom, filiere, niveau, role FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        return None

    # Récupération des compétences et lacunes
    cursor.execute("SELECT matiere FROM competences WHERE user_id = %s", (user_id,))
    matieres = [row['matiere'] for row in cursor.fetchall()]

    return {
        "id": user["id"],
        "nom": user["nom"],
        "prenom": user["prenom"],
        "filiere": user["filiere"] or "",
        "niveau": user["niveau"] or "",
        "skills": matieres,
        "availabilities": [],  # Optionnel : Ajoutez vos créneaux si présents en BDD
        "role": user["role"]
    }


# ─────────────────────────────────────────────
# ROUTES API OFFRES & DEMANDES
# ─────────────────────────────────────────────

@matching_bp.route("/offers", methods=["POST"])
def create_offer():
    if 'user_id' not in session:
        return jsonify({"error": "Non autorisé. Veuillez vous connecter."}), 401

    current_user_id = session['user_id']
    data = request.get_json(silent=True)
    if not data or not all(k in data for k in ["title", "description", "skills_offered"]):
        return jsonify({"error": "Données incomplètes ou invalides"}), 400

    connexion = get_db_connection()
    curseur = connexion.cursor()
    try:
        curseur.execute("""
            INSERT INTO offers (user_id, title, description, skills_offered, status)
            VALUES (%s, %s, %s, %s, 'active')
        """, (current_user_id, data["title"], data["description"], ",".join(data["skills_offered"])))
        connexion.commit()
        return jsonify({"message": "Offre créée avec succès !"}), 201
    except Exception as e:
        connexion.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        curseur.close()
        connexion.close()


@matching_bp.route("/offers", methods=["GET"])
def list_offers():
    if 'user_id' not in session:
        return jsonify({"error": "Non autorisé."}), 401

    connexion = get_db_connection()
    curseur = connexion.cursor(pymysql.cursors.DictCursor)
    try:
        curseur.execute("""
            SELECT o.id, o.user_id, o.title, o.description, o.skills_offered, u.nom, u.prenom, u.filiere, u.niveau
            FROM offers o
            JOIN users u ON o.user_id = u.id
            WHERE o.status = 'active'
        """)
        offres = curseur.fetchall()
        for o in offres:
            o["skills_offered"] = o["skills_offered"].split(",") if o["skills_offered"] else []
        return jsonify(offres), 200
    finally:
        curseur.close()
        connexion.close()


# ─────────────────────────────────────────────
# ROUTE PRINCIPALE : GET /matching/<user_id>
# ─────────────────────────────────────────────

@matching_bp.route("/matching/<int:user_id>", methods=["GET"])
def get_matches(user_id):
    """Retourne les profils compatibles classés par pertinence."""
    if 'user_id' not in session:
        return jsonify({"error": "Non autorisé."}), 401

    connexion = get_db_connection()
    curseur = connexion.cursor(pymysql.cursors.DictCursor)
    try:
        current_profile = get_user_matching_profile(user_id, curseur)
        if not current_profile:
            return jsonify({"error": "Utilisateur introuvable"}), 404

        # Récupère tous les candidats ayant un rôle différent (un Mentor cherche un Étudiant, et inversement)
        curseur.execute("SELECT id FROM users WHERE id != %s AND role != %s", (user_id, current_profile["role"]))
        candidate_ids = [row["id"] for row in curseur.fetchall()]

        results = []
        for c_id in candidate_ids:
            candidate_profile = get_user_matching_profile(c_id, curseur)
            if candidate_profile:
                score = compute_score(current_profile, candidate_profile)
                if score > 0:
                    candidate_profile["score"] = score
                    results.append(candidate_profile)

        # Tri décroissant selon le barème de score
        results.sort(key=lambda x: x["score"], reverse=True)

        return jsonify({
            "user_id": user_id,
            "total": len(results),
            "matches": results
        }), 200

    except Exception as e:
        return jsonify({"error": f"Erreur lors du calcul du matching : {str(e)}"}), 500
    finally:
        curseur.close()
        connexion.close()


# Pour l'appel direct (uniquement via la fonction utilitaire de match)
def get_matching_by_users(user_id_1, user_id_2):
    """Fonction de compatibilité pour chat.py (Vérifie s'ils partagent un score minimum)"""
    connexion = get_db_connection()
    curseur = connexion.cursor(pymysql.cursors.DictCursor)
    try:
        p1 = get_user_matching_profile(user_id_1, curseur)
        p2 = get_user_matching_profile(user_id_2, curseur)
        if p1 and p2 and p1["role"] != p2["role"]:
            return compute_score(p1, p2) > 0
        return False
    finally:
        curseur.close()
        connexion.close()