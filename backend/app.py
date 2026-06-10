import os
import pymysql
from flask import Flask, jsonify, render_template, session, Blueprint, request, redirect
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(basedir, '../frontend/templates'),
    static_folder=os.path.join(basedir, '../frontend/static'),
    static_url_path='/static'
)

load_dotenv()
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", os.getenv("SECRET_KEY", "mentorlink2026"))
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

from config.database import get_db_connection

# Import des Blueprints
from routes.auth import auth_bp
from routes.profile import profile_bp

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(profile_bp)

# ═══════════════════════════════════════════════════════
# ROUTES PAGES HTML (SIMPLIFIÉES)
# ═══════════════════════════════════════════════════════

@app.route("/")
def home():
    return render_template("Accueil.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/profile")
def profile_page():
    """Page profil - vérifie juste si connecté"""
    if "user_id" not in session:
        return redirect("/login")
    return render_template("profile.html")

@app.route("/matching")
def matching_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("matching.html")

@app.route("/chat")
def chat_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("chat.html")

@app.route("/offers")
def offers_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("offers.html")

@app.route('/api/matching', methods=['GET'])
def get_matching():
    """Retourne les meilleurs matchs pour l'utilisateur connecté"""
    if "user_id" not in session:
        return jsonify({"message": "Non connecté"}), 401
    
    current_user_id = session["user_id"]
    
    # Récupérer les paramètres de filtre
    matiere = request.args.get('matiere', '')
    filiere = request.args.get('filiere', '')
    type_user = request.args.get('type', '')
    
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Récupérer l'utilisateur actuel
        cur.execute("""
            SELECT id, nom, prenom, filiere, niveau, role
            FROM users 
            WHERE id = %s
        """, (current_user_id,))
        current_user = cur.fetchone()
        
        if not current_user:
            return jsonify({"message": "Utilisateur non trouvé"}), 404
        
        # Récupérer tous les autres utilisateurs (sauf soi-même)
        query = """
            SELECT id, nom, prenom, filiere, niveau, role
            FROM users 
            WHERE id != %s
        """
        params = [current_user_id]
        
        if filiere:
            query += " AND filiere = %s"
            params.append(filiere)
        
        if type_user:
            query += " AND role = %s"
            params.append(type_user)
        
        cur.execute(query, params)
        all_users = cur.fetchall()
        
        matches = []
        
        for user in all_users:
            # Calculer le score de compatibilité
            score = calculate_matching_score(current_user, user, cur)
            
            if score > 0:  # Ne retourner que les matchs avec score > 0
                # Récupérer les compétences de l'utilisateur
                cur.execute("""
                    SELECT c.nom_competence
                    FROM competences c
                    JOIN user_competences uc ON c.id = uc.id_competence
                    WHERE uc.user_id = %s AND uc.type = 'mentor'
                """, (user['id'],))
                competences = [row['nom_competence'] for row in cur.fetchall()]
                
                # Récupérer les disponibilités
                cur.execute("""
                    SELECT jour, heure_debut, heure_fin
                    FROM disponibilite
                    WHERE user_id = %s
                    LIMIT 3
                """, (user['id'],))
                disponibilites_rows = cur.fetchall()
                disponibilites = ', '.join([f"{d['jour']} {d['heure_debut']}-{d['heure_fin']}" 
                                           for d in disponibilites_rows])
                
                matches.append({
                    'id': user['id'],
                    'nom': user['nom'],
                    'prenom': user['prenom'],
                    'filiere': user['filiere'],
                    'niveau': user['niveau'],
                    'role': user['role'],
                    'score': score,
                    'competences': competences,
                    'disponibilites': disponibilites
                })
        
        # Trier par score décroissant
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return jsonify(matches), 200
        
    except Exception as e:
        print(f"Erreur matching: {e}")
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()


def calculate_matching_score(user_a, user_b, cursor):
    """
    Calcule le score de compatibilité entre deux utilisateurs
    """
    score = 0
    
    # +40 pts par compétence commune
    cursor.execute("""
        SELECT c.nom_competence
        FROM competences c
        JOIN user_competences uc ON c.id = uc.id_competence
        WHERE uc.user_id = %s
    """, (user_a['id'],))
    skills_a = set(row['nom_competence'] for row in cursor.fetchall())
    
    cursor.execute("""
        SELECT c.nom_competence
        FROM competences c
        JOIN user_competences uc ON c.id = uc.id_competence
        WHERE uc.user_id = %s
    """, (user_b['id'],))
    skills_b = set(row['nom_competence'] for row in cursor.fetchall())
    
    common_skills = skills_a & skills_b
    score += len(common_skills) * 40
    
    # +30 pts par créneau horaire commun
    cursor.execute("""
        SELECT jour, heure_debut, heure_fin
        FROM disponibilite
        WHERE user_id = %s
    """, (user_a['id'],))
    slots_a = cursor.fetchall()
    
    cursor.execute("""
        SELECT jour, heure_debut, heure_fin
        FROM disponibilite
        WHERE user_id = %s
    """, (user_b['id'],))
    slots_b = cursor.fetchall()
    
    common_slots = 0
    for slot_a in slots_a:
        for slot_b in slots_b:
            if (slot_a['jour'] == slot_b['jour'] and 
                slot_a['heure_debut'] == slot_b['heure_debut'] and 
                slot_a['heure_fin'] == slot_b['heure_fin']):
                common_slots += 1
    
    score += common_slots * 30
    
    # +20 pts si même filière
    if user_a['filiere'] == user_b['filiere']:
        score += 20
    
    # +10 pts si niveau adjacent
    niveau_map = {'L1': 1, 'L2': 2, 'L3': 3, 'M1': 4, 'M2': 5}
    niv_a = niveau_map.get(user_a['niveau'], 0)
    niv_b = niveau_map.get(user_b['niveau'], 0)
    
    if abs(niv_a - niv_b) <= 1:
        score += 10
    
    return score

# ═══════════════════════════════════════════════════════
# ROUTES CHAT / MESSAGERIE
# ═══════════════════════════════════════════════════════

@app.route("/api/chat/conversations", methods=["GET"])
def get_conversations():
    """Liste les conversations de l'utilisateur (regroupées par interlocuteur)"""
    if "user_id" not in session:
        return jsonify({"message": "Non connecté"}), 401
    
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Récupérer tous les interlocuteurs distincts
        cur.execute("""
            SELECT 
                CASE 
                    WHEN m.expediteur_id = %s THEN m.destinataire_id
                    ELSE m.expediteur_id
                END AS interlocuteur_id,
                MAX(m.timestamp) AS dernier_message_time
            FROM messages m
            WHERE m.expediteur_id = %s OR m.destinataire_id = %s
            GROUP BY interlocuteur_id
            ORDER BY dernier_message_time DESC
        """, (user_id, user_id, user_id))
        
        interlocuteurs = cur.fetchall()
        
        conversations = []
        for inter in interlocuteurs:
            inter_id = inter['interlocuteur_id']
            
            # Infos de l'interlocuteur
            cur.execute("""
                SELECT id, nom, prenom, email, filiere, niveau, role
                FROM users WHERE id = %s
            """, (inter_id,))
            user_info = cur.fetchone()
            
            # Dernier message
            cur.execute("""
                SELECT contenu, timestamp, expediteur_id
                FROM messages
                WHERE (expediteur_id = %s AND destinataire_id = %s)
                   OR (expediteur_id = %s AND destinataire_id = %s)
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user_id, inter_id, inter_id, user_id))
            last_msg = cur.fetchone()
            
            # Messages non lus
            cur.execute("""
                SELECT COUNT(*) as nb FROM messages
                WHERE expediteur_id = %s AND destinataire_id = %s AND is_read = 0
            """, (inter_id, user_id))
            unread = cur.fetchone()['nb']
            
            conversations.append({
                'interlocuteur_id': inter_id,
                'nom': user_info['nom'],
                'prenom': user_info['prenom'],
                'email': user_info['email'],
                'filiere': user_info.get('filiere', ''),
                'niveau': user_info.get('niveau', ''),
                'role': user_info.get('role', ''),
                'dernier_message': last_msg['contenu'] if last_msg else '',
                'dernier_message_time': str(last_msg['timestamp']) if last_msg else '',
                'non_lus': unread
            })
        
        return jsonify(conversations), 200
        
    except Exception as e:
        print(f"Erreur conversations: {e}")
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/api/chat/<int:interlocuteur_id>/messages", methods=["GET"])
def get_messages(interlocuteur_id):
    """Historique des messages avec un interlocuteur"""
    if "user_id" not in session:
        return jsonify({"message": "Non connecté"}), 401
    
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Récupérer les messages
        cur.execute("""
            SELECT m.id, m.contenu, m.timestamp, m.expediteur_id, m.is_read,
                   u.nom, u.prenom
            FROM messages m
            JOIN users u ON m.expediteur_id = u.id
            WHERE (m.expediteur_id = %s AND m.destinataire_id = %s)
               OR (m.expediteur_id = %s AND m.destinataire_id = %s)
            ORDER BY m.timestamp ASC
        """, (user_id, interlocuteur_id, interlocuteur_id, user_id))
        
        messages = cur.fetchall()
        
        # Marquer comme lus les messages reçus
        cur.execute("""
            UPDATE messages SET is_read = 1
            WHERE expediteur_id = %s AND destinataire_id = %s AND is_read = 0
        """, (interlocuteur_id, user_id))
        conn.commit()
        
        return jsonify(messages), 200
        
    except Exception as e:
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/api/chat/<int:interlocuteur_id>/send", methods=["POST"])
def send_message(interlocuteur_id):
    """Envoyer un message"""
    if "user_id" not in session:
        return jsonify({"message": "Non connecté"}), 401
    
    data = request.get_json()
    contenu = data.get('contenu', '').strip()
    
    if not contenu:
        return jsonify({"message": "Message vide"}), 400
    
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cur.execute("""
            INSERT INTO messages (expediteur_id, destinataire_id, contenu, is_read)
            VALUES (%s, %s, %s, 0)
        """, (user_id, interlocuteur_id, contenu))
        
        conn.commit()
        msg_id = cur.lastrowid
        
        # Récupérer le message complet
        cur.execute("""
            SELECT m.id, m.contenu, m.timestamp, m.expediteur_id,
                   u.nom, u.prenom
            FROM messages m
            JOIN users u ON m.expediteur_id = u.id
            WHERE m.id = %s
        """, (msg_id,))
        
        new_msg = cur.fetchone()
        
        # Diffusion SocketIO
        room_name = f"chat_{min(user_id, interlocuteur_id)}_{max(user_id, interlocuteur_id)}"
        socketio.emit('new_message', {
            'id': new_msg['id'],
            'contenu': new_msg['contenu'],
            'timestamp': str(new_msg['timestamp']),
            'expediteur_id': new_msg['expediteur_id'],
            'expediteur_nom': new_msg['nom'],
            'expediteur_prenom': new_msg['prenom']
        }, room=room_name)
        
        return jsonify(new_msg), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()


# ═══════════════════════════════════════════════════════
# SOCKETIO - MESSAGERIE TEMPS RÉEL
# ═══════════════════════════════════════════════════════

@socketio.on("connect")
def handle_connect():
    """Quand un client se connecte au WebSocket"""
    print(f"✅ Client WebSocket connecté: {request.sid}")
    if "user_id" in session:
        print(f"   → Utilisateur: {session['user_id']}")


@socketio.on("disconnect")
def handle_disconnect():
    """Quand un client se déconnecte"""
    print(f"❌ Client WebSocket déconnecté: {request.sid}")


@socketio.on("join_chat")
def handle_join_chat(data):
    """Rejoindre un salon de conversation entre 2 utilisateurs"""
    if "user_id" not in session:
        emit("error", {"message": "Non connecté"})
        return
    
    user1 = data.get("user1")
    user2 = data.get("user2")
    
    if not user1 or not user2:
        emit("error", {"message": "Données manquantes"})
        return
    
    # Room nommée de façon unique pour chaque paire d'utilisateurs
    room_name = f"chat_{min(int(user1), int(user2))}_{max(int(user1), int(user2))}"
    join_room(room_name)
    print(f"👤 Utilisateur {session['user_id']} a rejoint {room_name}")
    emit("joined", {"room": room_name, "user_id": session["user_id"]}, room=room_name)


@socketio.on("send_message_socket")
def handle_send_message(data):
    """Envoyer un message via WebSocket (temps réel)"""
    if "user_id" not in session:
        emit("error", {"message": "Non connecté"})
        return
    
    interlocuteur_id = data.get("interlocuteur_id")
    contenu = data.get("contenu", "").strip()
    
    if not interlocuteur_id or not contenu:
        emit("error", {"message": "Données manquantes"})
        return
    
    user_id = session["user_id"]
    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        
        # Insérer le message en BDD
        cur.execute("""
            INSERT INTO messages (expediteur_id, destinataire_id, contenu, is_read)
            VALUES (%s, %s, %s, 0)
        """, (user_id, interlocuteur_id, contenu))
        
        conn.commit()
        msg_id = cur.lastrowid
        
        # Récupérer le message complet avec infos expéditeur
        cur.execute("""
            SELECT m.id, m.contenu, m.timestamp, m.expediteur_id,
                   u.nom, u.prenom
            FROM messages m
            JOIN users u ON m.expediteur_id = u.id
            WHERE m.id = %s
        """, (msg_id,))
        
        msg = cur.fetchone()
        
        # Diffuser dans la room commune
        room_name = f"chat_{min(user_id, interlocuteur_id)}_{max(user_id, interlocuteur_id)}"
        
        emit("new_message", {
            'id': msg['id'],
            'contenu': msg['contenu'],
            'timestamp': str(msg['timestamp']),
            'expediteur_id': msg['expediteur_id'],
            'expediteur_nom': msg['nom'],
            'expediteur_prenom': msg['prenom']
        }, room=room_name)
        
        print(f"💬 Message envoyé de {user_id} vers {interlocuteur_id} (room: {room_name})")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erreur send_message_socket: {e}")
        emit("error", {"message": f"Erreur: {str(e)}"})
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/chat/users", methods=["GET"])
def get_all_users():
    """Liste tous les utilisateurs inscrits (sauf soi-même)"""
    if "user_id" not in session:
        return jsonify({"message": "Non connecté"}), 401
    
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cur.execute("""
            SELECT id, nom, prenom, email, filiere, niveau, role
            FROM users 
            WHERE id != %s
            ORDER BY nom, prenom
        """, (user_id,))
        
        users = cur.fetchall()
        return jsonify(users), 200
        
    except Exception as e:
        print(f"Erreur get_all_users: {e}")
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()
# ═══════════════════════════════════════════════════════
# DÉMARRAGE
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    port_serveur = int(os.getenv("PORT", 5000))
    print(f"\n{'='*60}")
    print(f"[*] Serveur MentorLink démarré sur le port {port_serveur} !")
    print(f"{'='*60}")
    socketio.run(app, host="0.0.0.0", port=port_serveur, debug=True)