document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('user_id');
    
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/matching/${userId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        const matches = await response.json();
        const container = document.getElementById('matching-results');
        
        if (matches.length === 0) {
            container.innerHTML = '<p>Aucun mentor trouvé pour le moment.</p>';
        } else {
            matches.forEach(match => {
                const card = `
                    <div class="match-card" style="border: 1px solid #ddd; padding: 15px; margin: 10px; border-radius: 8px;">
                        <h3>${match.prenom} ${match.nom}</h3>
                        <p>Filière: ${match.filiere} | Niveau: ${match.niveau}</p>
                        <p><strong>Score de compatibilité: ${match.score} pts</strong></p>
                        <button onclick="window.location.href='chat.html?mentor_id=${match.id}'">
                            Contacter
                        </button>
                    </div>
                `;
                container.innerHTML += card;
            });
        }
    } catch (error) {
        console.error('Erreur matching:', error);
    }
});