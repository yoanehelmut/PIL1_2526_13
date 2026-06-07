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
        # Récupère l'interlocuteur selon la position de l'utilisateur courant
        cur.execute("""
            SELECT
                c.id,
                CASE WHEN c.utilisateur1_id = %s THEN u2.nom ELSE u1.nom END AS interlocuteur_nom,
                CASE WHEN c.utilisateur1_id = %s THEN u2.id  ELSE u1.id  END AS interlocuteur_id
            FROM conversations c
            JOIN utilisateurs u1 ON u1.id = c.utilisateur1_id
            JOIN utilisateurs u2 ON u2.id = c.utilisateur2_id
            WHERE c.utilisateur1_id = %s OR c.utilisateur2_id = %s
            ORDER BY c.date_creation DESC
        """, (uid, uid, uid, uid))
        conversations = cur.fetchall()
    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

    return render_template("messagerie.html", conversations=conversations, user=session)


@messages_bp.route("/conversation/<int:conv_id>/messages")
def get_messages(conv_id):
    if "user_id" not in session:
        return jsonify({"error": "Non connecte"}), 401

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, u.nom, m.expediteur_id, m.contenu, m.date_envoi
            FROM messages m
            JOIN utilisateurs u ON u.id = m.expediteur_id
            WHERE m.conversation_id = %s
            ORDER BY m.date_envoi ASC
        """, (conv_id,))
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


@messages_bp.route("/conversation/nouvelle", methods=["POST"])
def nouvelle_conversation():
    if "user_id" not in session:
        return jsonify({"error": "Non connecte"}), 401

    data = request.get_json()
    if not data or "interlocuteur_id" not in data:
        return jsonify({"error": "interlocuteur_id manquant"}), 400

    interlocuteur_id = data["interlocuteur_id"]
    uid = session["user_id"]

    if uid == interlocuteur_id:
        return jsonify({"error": "Impossible de démarrer une conversation avec soi-même"}), 400

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM conversations
            WHERE (utilisateur1_id = %s AND utilisateur2_id = %s)
               OR (utilisateur1_id = %s AND utilisateur2_id = %s)
        """, (uid, interlocuteur_id, interlocuteur_id, uid))
        existing = cur.fetchone()

        if existing:
            return jsonify({"conversation_id": existing[0]})

        cur.execute(
            "INSERT INTO conversations (utilisateur1_id, utilisateur2_id) VALUES (%s, %s) RETURNING id",
            (uid, interlocuteur_id)
        )
        conv_id = cur.fetchone()[0]
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

    return jsonify({"conversation_id": conv_id})