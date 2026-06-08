from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
import psycopg2, os

messages_bp = Blueprint("messages", __name__)

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "mentorlink"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        port=os.getenv("DB_PORT", "5432")
    )

@messages_bp.route("/messagerie")
def messagerie():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    uid = session["user_id"]
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT
                CASE WHEN m.expediteur_id = %s THEN m.destinataire_id ELSE m.expediteur_id END AS interlocuteur_id,
                u.nom
            FROM messages m
            JOIN users u ON u.id = CASE WHEN m.expediteur_id = %s THEN m.destinataire_id ELSE m.expediteur_id END
            WHERE m.expediteur_id = %s OR m.destinataire_id = %s
        """, (uid, uid, uid, uid))
        conversations = cur.fetchall()
    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
    return render_template("messagerie.html", conversations=conversations, user=session)

@messages_bp.route("/conversation/<int:interlocuteur_id>/messages")
def get_messages(interlocuteur_id):
    if "user_id" not in session:
        return jsonify({"error": "Non connecte"}), 401
    uid = session["user_id"]
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, u.nom, m.expediteur_id, m.contenu, m.timestamp
            FROM messages m
            JOIN users u ON u.id = m.expediteur_id
            WHERE (m.expediteur_id = %s AND m.destinataire_id = %s)
               OR (m.expediteur_id = %s AND m.destinataire_id = %s)
            ORDER BY m.timestamp ASC
        """, (uid, interlocuteur_id, interlocuteur_id, uid))
        msgs = [
            {"id": r[0], "expediteur": r[1], "expediteur_id": r[2], "contenu": r[3], "date": str(r[4])}
            for r in cur.fetchall()
        ]
    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
    return jsonify(msgs)

@messages_bp.route("/message/envoyer", methods=["POST"])
def envoyer_message():
    if "user_id" not in session:
        return jsonify({"error": "Non connecte"}), 401
    data = request.get_json()
    if not data or "destinataire_id" not in data or "contenu" not in data:
        return jsonify({"error": "Données manquantes"}), 400s
    destinataire_id = data["destinataire_id"]
    uid = session["user_id"]
    if uid == destinataire_id:
        return jsonify({"error": "Impossible d'envoyer un message à soi-même"}), 400
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (expediteur_id, destinataire_id, contenu) VALUES (%s, %s, %s) RETURNING id, timestamp",
            (uid, destinataire_id, data["contenu"])
        )
        row = cur.fetchone()
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
    return jsonify({"id": row[0], "timestamp": str(row[1])})