CREATE DATABASE IF NOT EXISTS mentorlink 
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE mentorlink;

CREATE utilisateurs (
    id_utilisateur    INT             AUTO_INCREMENT PRIMARY KEY,
    nom               VARCHAR(100)    NOT NULL,
    prenom            VARCHAR(100)    NOT NULL,
    email             VARCHAR(200)    NOT NULL UNIQUE,
    telephone         VARCHAR(20)     NOT NULL UNIQUE,
    mot de passe      VARCHAR(200)    NOT NULL,
    filiere           ENUM('IA','GL','SE_IOT','SI') NOT NULL,
    niveaus           ENUM('L1','L2','L3','M1','M2') NOT NULL,
    photo_profil      VACHAR(255)     DEFAULT NULL,
    desc              TEXT            DEFAULT NULL,
    date-inscription  DATETIME        NOT NULL DEFAULT   CURRENT_TIMESTAMP
);

CREATE TABLE  user-competences (
    id_utilisateur     INT             NOT NULL,
    id_competence      INT             NOT NULL,
    niv_competence     ENUM('fort','faible')  NOT NULL,
    PRIMARY KEY (id_utilisateur, id_competence, niv_competence),
    FOREIGN KEY (id_utilisateur)  REFERENCES utilisateurs(id_utilisateur) 
       ON DELETE CASCADE,
    FOREIGN KEY (id_competence) REFERENCES competence(id_competence)
       ON DELETE CASCADE 
);
CREATE TABLE disponibilites (
    id_disponibilite     INT         AUTO_INCREMENT PRIMARY KEY
    id_utilisateur       INT          NOT NULL,
    jour_semaine         ENUM('Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche')  NOT NULL,
    heure_deb            TIME         NOT NULL,
    heure_fin            TIME         NOT NULL,
    FOREIGN KEY (id_utilisateur)  REFERENCES utilisateurs(id_utilisateur)
              ON DELETE CASCADE
);
CREATE TABLE Mentorat (
    id_offre      INT               AUTO_INCREMENT  PRIMARY KEY,
    id_utilisateur INT                NOT NULL,
    typt_offre     ENUM('mentor','mentoré')  NOT NULL,

)

CREATE TABLE offres_mentorat (
    id_offre         INT           AUTO_INCREMENT PRIMARY KEY,
    id_utilisateur   INT           NOT NULL,
    type_offre       ENUM('offre','demande') NOT NULL,
    description      TEXT          DEFAULT NULL,
    format           ENUM('presentiel','en_ligne','les_deux') NOT NULL,
    statut           ENUM('active','inactive','archivee') NOT NULL DEFAULT 'active',
    date_creation    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_utilisateur) REFERENCES utilisateurs(id_utilisateur)
        ON DELETE CASCADE
);

-- ============================================================
-- TABLE : offre_competences (N:N offres ↔️ competences)
-- ============================================================
CREATE TABLE offre_competences (
    id_offre         INT           NOT NULL,
    id_competence    INT           NOT NULL,
    PRIMARY KEY (id_offre, id_competence),
    FOREIGN KEY (id_offre)        REFERENCES offres_mentorat(id_offre)
        ON DELETE CASCADE,
    FOREIGN KEY (id_competence)  REFERENCES competences(id_competence)
        ON DELETE CASCADE
);

CREATE TABLE matchings (
    id_matching          INT             AUTO_INCREMENT PRIMARY KEY,
    id_mentor            INT             NOT NULL,
    id_mentore           INT             NOT NULL,
    id_offre             INT             NOT NULL,
    score_compatibilite  DECIMAL(5,2)   NOT NULL,
    statut               ENUM('propose','accepte','refuse','termine')
                                         NOT NULL DEFAULT 'propose',
    date_matching        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mentor)  REFERENCES utilisateurs(id_utilisateur),
    FOREIGN KEY (id_mentore) REFERENCES utilisateurs(id_utilisateur),
    FOREIGN KEY (id_offre)   REFERENCES offres_mentorat(id_offre)
);

CREATE TABLE conversations (
    id_conversation   INT      AUTO_INCREMENT PRIMARY KEY,
    id_matching       INT      NOT NULL UNIQUE,
    date_creation     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    derniere_activite DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_matching) REFERENCES matchings(id_matching)
        ON DELETE CASCADE
);

CREATE TABLE messages (
    id_message        INT      AUTO_INCREMENT PRIMARY KEY,
    id_conversation   INT      NOT NULL,
    id_expediteur     INT      NOT NULL,
    contenu           TEXT     NOT NULL,
    date_envoi        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lu                BOOLEAN  NOT NULL DEFAULT FALSE,
    FOREIGN KEY (id_conversation) REFERENCES conversations(id_conversation)
        ON DELETE CASCADE,
    FOREIGN KEY (id_expediteur)   REFERENCES utilisateurs(id_utilisateur)
);

CREATE INDEX idx_messages_conv    ON messages(id_conversation);
CREATE INDEX idx_messages_date    ON messages(date_envoi);
CREATE INDEX idx_matchings_mentor ON matchings(id_mentor);
CREATE INDEX idx_matchings_mentoreON matchings(id_mentore);
CREATE INDEX idx_offres_statut    ON offres_mentorat(statut);
CREATE INDEX idx_dispos_user      ON disponibilites(id_utilisateur);
          