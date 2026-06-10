// ============================================
// GESTION DE LA CONNEXION (Adapté à auth.py)
// ============================================
const loginForm = document.getElementById('loginForm');

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const zoneResultat = document.getElementById('resultat');

        try {
            const response = await fetch('http://127.0.0.1:5000/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include', // 📍 INDISPENSABLE pour les sessions Flask
                body: JSON.stringify({ email: email, password: password })
            });

            const data = await response.json();
            
            if (response.ok) {
                // ✅ SUCCÈS : auth.py renvoie juste {"message": "Connexion OK"}
                if (zoneResultat) {
                    zoneResultat.style.backgroundColor = '#d4edda';
                    zoneResultat.style.color = '#155724';
                    zoneResultat.style.display = 'block';
                    zoneResultat.innerText = "✅ " + data.message;
                }
                
                // Redirection après 1 seconde (Pas besoin de stocker de token)
                setTimeout(() => {
                    window.location.href = '/profile'; // Assurez-vous d'avoir cette route dans app.py
                }, 1000);
                
            } else {
                if (zoneResultat) {
                    zoneResultat.style.backgroundColor = '#f8d7da';
                    zoneResultat.style.color = '#721c24';
                    zoneResultat.style.display = 'block';
                    zoneResultat.innerText = "❌ " + data.message;
                }
            }
        } catch (error) {
            console.error('Erreur:', error);
            if (zoneResultat) {
                zoneResultat.style.backgroundColor = '#f8d7da';
                zoneResultat.style.color = '#721c24';
                zoneResultat.style.display = 'block';
                zoneResultat.innerText = "❌ Serveur injoignable !";
            }
        }
    });
}

// ============================================
// GESTION DE L'INSCRIPTION
// ============================================
const registerForm = document.getElementById('formInscription'); // ⚠️ Attention à l'ID exact dans register.html

if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            nom: document.getElementById('nom').value,
            prenom: document.getElementById('prenom').value,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value, // Correspond à auth.py
            role: "etudiant",
            filiere: document.getElementById('filiere').value,
            niveau: document.getElementById('niveau').value
        };

        const zoneResultat = document.getElementById('resultat');

        try {
            const response = await fetch('http://127.0.0.1:5000/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            
            if (response.ok) {
                if (zoneResultat) {
                    zoneResultat.style.backgroundColor = '#d4edda';
                    zoneResultat.style.color = '#155724';
                    zoneResultat.style.display = 'block';
                    zoneResultat.innerText = "✅ " + data.message;
                }
                setTimeout(() => { window.location.href = '/login'; }, 2000);
            } else {
                if (zoneResultat) {
                    zoneResultat.style.backgroundColor = '#f8d7da';
                    zoneResultat.style.color = '#721c24';
                    zoneResultat.style.display = 'block';
                    zoneResultat.innerText = " " + data.message;
                }
            }
        } catch (error) {
            console.error('Erreur:', error);
            if (zoneResultat) {
                zoneResultat.style.backgroundColor = '#f8d7da';
                zoneResultat.style.color = '#721c24';
                zoneResultat.style.display = 'block';
                zoneResultat.innerText = "❌ Serveur injoignable !";
            }
        }
    });
}