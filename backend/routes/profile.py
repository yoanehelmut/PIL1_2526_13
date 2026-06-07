from flask import Blueprint, render_template, request, redirect, url_for, flash, session
# Remplacer par votre système de gestion de base de données (ex: import depuis database.py)
from database import get_db_connection  

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/', methods=['GET'])
def view_my_profile():
    """Affiche le profil de l'utilisateur connecté."""
    if 'user_id' not in session:
        flash("Veuillez vous connecter pour accéder à votre profil.", "danger")
        return redirect('/auth/login')
        
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Récupération des infos utilisateur de l'IFRI
    cursor.execute("SELECT nom, prenom, email, telephone, filiere, niveau, bio, photo FROM utilisateurs WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    # Récupération des compétences (points forts) et lacunes (points faibles)
    cursor.execute("SELECT matiere FROM competences WHERE user_id = %s AND type = 'fort'", (user_id,))
    competences = [row['matiere'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT matiere FROM competences WHERE user_id = %s AND type = 'faible'", (user_id,))
    lacunes = [row['matiere'] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template('profile/view.html', user=user, competences=competences, lacunes=lacunes)


@profile_bp.route('/edit', methods=['GET', 'POST'])
def edit_profile():
    """Permet à l'étudiant de modifier ses informations de profil."""
    if 'user_id' not in session:
        return redirect('/auth/login')
        
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Récupération des champs du formulaire
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        filiere = request.form.get('filiere')
        niveau = request.form.get('niveau')
        bio = request.form.get('bio')
        
        # Mise à jour des informations de base
        cursor.execute("""
            UPDATE utilisateurs 
            SET nom = %s, prenom = %s, filiere = %s, niveau = %s, bio = %s 
            WHERE id = %s
        """, (nom, prenom, filiere, niveau, bio, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("Profil mis à jour avec succès !", "success")
        return redirect('/profile/')
        
    # En cas de GET, récupérer les données actuelles pour pré-remplir le formulaire
    cursor.execute("SELECT * FROM utilisateurs WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('profile/edit.html', user=user)