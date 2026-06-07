from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from config.database import get_db_connection

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/', methods=['GET'])
def view_my_profile():
    """Affiche le profil de l'utilisateur connecté."""
    if 'user_id' not in session:
        flash("Veuillez vous connecter pour accéder à votre profil.", "danger")
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Récupération des infos utilisateur
    cursor.execute("SELECT nom, prenom, email, telephone, filiere, niveau, bio, photo FROM utilisateurs WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    # Récupération des compétences (points forts)
    cursor.execute("SELECT matiere FROM competences WHERE user_id = %s AND type = 'fort'", (user_id,))
    competences = [row['matiere'] for row in cursor.fetchall()]
    
    # Récupération des lacunes (points faibles)
    cursor.execute("SELECT matiere FROM competences WHERE user_id = %s AND type = 'faible'", (user_id,))
    lacunes = [row['matiere'] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template('profile/view.html', user=user, competences=competences, lacunes=lacunes)


@profile_bp.route('/edit', methods=['GET', 'POST'])
def edit_profile():
    """Permet à l'étudiant de modifier ses informations de profil."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        filiere = request.form.get('filiere')
        niveau = request.form.get('niveau')
        bio = request.form.get('bio')
        
        cursor.execute("""
            UPDATE utilisateurs 
            SET nom = %s, prenom = %s, filiere = %s, niveau = %s, bio = %s 
            WHERE id = %s
        """, (nom, prenom, filiere, niveau, bio, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("Profil mis à jour avec succès !", "success")
        return redirect(url_for('profile.view_my_profile'))
        
    # GET : pré-remplir le formulaire
    cursor.execute("SELECT * FROM utilisateurs WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('profile/edit.html', user=user)