CREATE TABLE users (
id INT AUTO_INCREMENT PRIMARY KEY,
nom VARCHAR(100) NOT NULL,
prenom VARCHAR(100) NOT NULL,
email VARCHAR (150) UNIQUE NOT NULL,
mot_de_passe_hash TEXT NOT NULL,
filiere VARCHAR(100),
niveau VARCHAR(50),
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE competences (
id INT AUTO_INCREMENT PRIMARY KEY,
nom VARCHAR(100) NOT NULL
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
type VARCHAR(10)NOT NULL,
description TEXT,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY (user_id)
REFERENCES users(id)
ON DELETE CASCADE
);

CREATE TABLE matchings (
id INT AUTO_INCREMENT PRIMARY KEY,
user1_id INT NOT NULL,
user2_id INT NOT NULL,
score DECIMAL(5,2),
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY (user1_id)
REFERENCES users(id)
ON DELETE CASCADE
);

CREATE TABLE messages (
id INT AUTO_INCREMENT PRIMARY KEY,
expediteur_id INT NOT NULL,
destinataire_id INT NOT NULL,
contenu TEXT NOT NULL,
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY (expediteur_id)
REFERENCES users(id)
ON DELETE CASCADE,

FOREIGN KEY (destinataire_id)
REFERENCES users(id)
ON DELETE CASCADE
);
