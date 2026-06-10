# 🎓 MentorLink

Plateforme de mentorat académique mettant en relation mentors et mentorés selon leurs compétences, leur filière et leur niveau d’étude.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey) ![MySQL](https://img.shields.io/badge/MySQL-8.0-orange) ![Groupe](https://img.shields.io/badge/Groupe-13-green)

-----

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Technologies](#-technologies-utilisées)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Lancer le projet](#-lancer-le-projet)
- [Structure du projet](#-structure-du-projet)
- [API Endpoints](#-api-endpoints)
- [Auteurs](#-auteurs)

-----

## 🚀 Fonctionnalités

### 👤 Gestion des utilisateurs

- Inscription et connexion sécurisées (mot de passe hashé avec Bcrypt)
- Gestion du profil utilisateur
- Modification des informations personnelles
- Gestion des compétences

### 🔗 Matching intelligent

- Recherche automatique de profils compatibles
- Score de compatibilité basé sur :
 - Les compétences communes
 - La filière
 - Le niveau d’étude
 - Les disponibilités

### 📋 Offres et demandes

- Publication d’offres de mentorat
- Publication de demandes d’accompagnement
- Consultation des offres disponibles
- Réponse aux publications

### 💬 Messagerie temps réel

- Communication entre mentors et mentorés
- Conversations privées
- Interface de chat avec Flask-SocketIO

-----

## 🛠️ Technologies utilisées

|Couche             |Technologies                                           |
|-------------------|-------------------------------------------------------|
|**Frontend**       |HTML5, CSS3, JavaScript                                |
|**Backend**        |Python, Flask, Flask-CORS, Flask-Bcrypt, Flask-SocketIO|
|**Base de données**|MySQL, PyMySQL                                         |

-----

## ✅ Prérequis

Avant de commencer, assurez-vous d’avoir installé :

- [Python 3.10+](https://www.python.org/downloads/)
- [MySQL 8.0+](https://dev.mysql.com/downloads/)
- `pip` (inclus avec Python)
- Git

-----

## 📦 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/MentorLink.git
cd MentorLink
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

-----

## ⚙️ Configuration

### 1. Créer la base de données MySQL

Connectez-vous à MySQL et exécutez :

```sql
CREATE DATABASE mentorlink CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Configurer les variables d’environnement

Copiez le fichier exemple et remplissez vos informations :

```bash
cp .env.example .env
```

Contenu du fichier `.env` :

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_NAME=mentorlink

SECRET_KEY=une_cle_secrete_longue_et_aleatoire
FLASK_ENV=development
```

-----

## ▶️ Lancer le projet

```bash
python app.py
```

L’application sera accessible à l’adresse : <http://localhost:5000>

⚠️ Ne pas ouvrir les fichiers HTML directement dans le navigateur (`C:/...`), cela empêche la communication avec le serveur Flask.

-----

## 📁 Structure du projet

```text
MentorLink/
│
├── app.py                  # Point d'entrée de l'application
│
├── config/
│   └── database.py         # Connexion à la base de données
│
├── routes/
│   ├── auth.py             # Inscription / Connexion
│   ├── matching.py         # Algorithme de matching
│   └── messages.py         # Messagerie
│
├── templates/
│   ├── Accueil.html
│   ├── profile.html
│   ├── matching.html
│   ├── offers.html
│   └── chat.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── matching.js
│       ├── offers.js
│       └── chat.js
│
├── .env                    # Variables d'environnement (non versionné)
├── .env.example            # Exemple de configuration
├── requirements.txt        # Dépendances Python
└── README.md
```

-----

## 🔌 API Endpoints

|Méthode|Route           |Description                              |
|-------|----------------|-----------------------------------------|
|`GET`  |`/`             |Vérification que l’API est opérationnelle|
|`POST` |`/auth/register`|Inscription d’un utilisateur             |
|`POST` |`/auth/login`   |Connexion                                |
|`GET`  |`/profile`      |Récupérer le profil                      |
|`PUT`  |`/profile`      |Modifier le profil                       |
|`GET`  |`/matching`     |Obtenir les profils compatibles          |
|`GET`  |`/offers`       |Lister les offres                        |
|`POST` |`/offers`       |Publier une offre                        |
|`GET`  |`/messages/<id>`|Récupérer une conversation               |
|`POST` |`/messages`     |Envoyer un message                       |

-----

## 👥 Auteurs

Projet réalisé dans le cadre du cours **PIL1-2025-2026** — **Groupe 13**


-----

