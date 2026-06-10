CREATE TABLE users (
id INT AUTO_INCREMENT PRIMARY KEY,
nom VARCHAR(100) NOT NULL,
prenom VARCHAR(100) NOT NULL,
email VARCHAR (150) UNIQUE NOT NULL,
mot_de_passe_hash TEXT NOT NULL,
role ENUM('mentor','etudiant')NOT NULL,
filiere VARCHAR(100),
niveau VARCHAR(50),
reset_token VARCHAR(255)NULL,
reset_token_expires TIMESTAMP NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE competences (
id INT AUTO_INCREMENT PRIMARY KEY,
nom VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE user_competences (
user_id INT,
competence_id INT,

PRIMARY KEY(user_id,competence_id),

FOREIGN KEY (user_id)
REFERENCES users(id)
ON DELETE CASCADE,

FOREIGN KEY (competence_id)
REFERENCES competences(id)
ON DELETE CASCADE
);

CREATE TABLE disponibilites (
id INT AUTO_INCREMENT PRIMARY KEY,
user_id INT NOT NULL,
jour VARCHAR(20)NOT NULL,
heure_debut TIME NOT NULL,
heure_fin TIME NOT NULL,

FOREIGN KEY (user_id)
REFERENCES users(id)
ON DELETE CASCADE
);

CREATE TABLE offres_demandes (
id INT AUTO_INCREMENT PRIMARY KEY,
user_id INT NOT NULL,
type ENUM ('offre','demande') NOT NULL,
description TEXT,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY (user_id)
REFERENCES users(id)
ON DELETE CASCADE
);

CREATE TABLE matchings (
id INT AUTO_INCREMENT PRIMARY KEY,
etudiant_id INT NOT NULL,
mentor_id INT NOT NULL,
score DECIMAL(5,2) NOT NULL,
statut ENUM('en_attente','accepte','refuse') DEFAULT 'en_attente',
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
FOREIGN KEY (etudiant_id)
REFERENCES users(id)
ON DELETE CASCADE,
FOREIGN KEY (mentor_id)
REFERENCES users(id)
ON DELETE CASCADE

);

CREATE TABLE messages (
id INT AUTO_INCREMENT PRIMARY KEY,
expediteur_id INT NOT NULL,
destinataire_id INT NOT NULL,
contenu TEXT NOT NULL,
is_read BOOLEAN DEFAULT FALSE,
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY (expediteur_id)
REFERENCES users(id)
ON DELETE CASCADE,

FOREIGN KEY (destinataire_id)
REFERENCES users(id)
ON DELETE CASCADE
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_matching_score ON matchings(score);

-- ============================================
-- TABLES MANQUANTES - À exécuter dans phpMyAdmin
-- ============================================

-- 1️⃣ Table des compétences (référentiel)
CREATE TABLE IF NOT EXISTS competences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom_competence VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2️⃣ Table de liaison utilisateurs-compétences
CREATE TABLE IF NOT EXISTS user_competences (
    user_id INT NOT NULL,
    competence_id INT NOT NULL,
    type ENUM('mentor', 'mentore') NOT NULL DEFAULT 'mentore',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, competence_id, type),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (competence_id) REFERENCES competences(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- DONNÉES DE TEST (optionnel)
-- ============================================
INSERT INTO competences (nom_competence) VALUES 
('Python'),
('SQL'),
('Machine Learning'),
('Algorithmique'),
('Base de données'),
('Java'),
('JavaScript'),
('HTML/CSS'),
('Réseau'),
('Mathématiques')
ON DUPLICATE KEY UPDATE nom_competence = nom_competence;