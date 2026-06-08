from flask import Flask, render_template, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from flask_bcrypt import Bcrypt
import mysql.connector, os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "mentorlink2026")
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "mentorlink"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        port=int(os.getenv("DB_PORT", "3306"))
    )

from routes.auth import auth_bp
from routes.messages import messages_bp
app.register_blueprint(auth_bp)
app.register_blueprint(messages_bp)

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth.login"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html", user=session)

@socketio.on("rejoindre_conversation")
def rejoindre(data):
    join_room(str(data["conversation_id"]))

@socketio.on("envoyer_message")
def envoyer(data):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (conversation_id, expediteur_id, contenu) VALUES (%s, %s, %s)",
            (data["conversation_id"], data["expediteur_id"], data["contenu"])
        )
        conn.commit()
        msg_id = cur.lastrowid
        cur.execute("SELECT date_envoi FROM messages WHERE id = %s", (msg_id,))
        date_envoi = cur.fetchone()[0]
        cur.close()
        conn.close()
        emit("nouveau_message", {
            "id": msg_id,
            "expediteur_id": data["expediteur_id"],
            "expediteur_nom": data["expediteur_nom"],
            "contenu": data["contenu"],
            "date_envoi": str(date_envoi)
        }, room=str(data["conversation_id"]))
    except Exception as e:
        emit("erreur", {"message": str(e)})

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)