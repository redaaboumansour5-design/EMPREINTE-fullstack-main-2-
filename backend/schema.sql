-- ============================================================================
-- schema.sql — Schéma de référence SQL Server pour EMPREINTE (Pointage IA)
-- ============================================================================
-- Ce script est fourni à titre de RÉFÉRENCE / documentation : au démarrage,
-- l'application crée déjà automatiquement les tables via SQLAlchemy
-- (db.create_all() dans seed.py). Utilisez ce script si vous préférez créer
-- le schéma manuellement dans SQL Server Management Studio (SSMS) avant de
-- lancer l'application, ou pour le versionner dans un outil de migration.
--
-- Exécution : ouvrez ce fichier dans SSMS (connecté à votre instance), ou :
--   sqlcmd -S localhost\SQLEXPRESS -d EmpreintePointage -U sa -P *** -i schema.sql
-- ============================================================================

IF DB_ID('EmpreintePointage') IS NULL
    CREATE DATABASE EmpreintePointage;
GO
USE EmpreintePointage;
GO

-- ---------------------------------------------------------------------------
-- Administrateur
-- ---------------------------------------------------------------------------
CREATE TABLE administrateurs (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    identifiant_admin   NVARCHAR(50)  NOT NULL UNIQUE,
    mot_de_passe_hash   NVARCHAR(255) NOT NULL,
    nom_complet         NVARCHAR(150) NULL,
    date_creation       DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
);

-- ---------------------------------------------------------------------------
-- Departement  (le FK vers responsable est ajouté après utilisateurs, cyclique)
-- ---------------------------------------------------------------------------
CREATE TABLE departements (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    nom             NVARCHAR(100) NOT NULL UNIQUE,
    responsable_id  INT NULL,
    date_creation   DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- ---------------------------------------------------------------------------
-- Utilisateur (employé / manager / RH — distingués par le champ role)
-- ---------------------------------------------------------------------------
CREATE TABLE utilisateurs (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    matricule           NVARCHAR(20)  NOT NULL UNIQUE,
    nom                 NVARCHAR(100) NOT NULL,
    prenom              NVARCHAR(100) NOT NULL,
    email               NVARCHAR(150) NOT NULL UNIQUE,
    mot_de_passe_hash   NVARCHAR(255) NOT NULL,
    telephone           NVARCHAR(30)  NULL,
    role                NVARCHAR(20)  NOT NULL DEFAULT 'employe'
                            CONSTRAINT ck_utilisateur_role CHECK (role IN ('employe','manager','rh')),
    poste               NVARCHAR(100) NULL,
    date_embauche       DATE          NULL,
    date_creation       DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
    departement_id      INT           NULL,
    CONSTRAINT fk_utilisateur_departement FOREIGN KEY (departement_id) REFERENCES departements(id)
);

ALTER TABLE departements
    ADD CONSTRAINT fk_departement_responsable FOREIGN KEY (responsable_id) REFERENCES utilisateurs(id);

-- ---------------------------------------------------------------------------
-- Permission — table plate (role, action) consultée par verifierDroit(action)
-- ---------------------------------------------------------------------------
CREATE TABLE permissions (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    nom_role            NVARCHAR(20)  NOT NULL,
    action_autorisee    NVARCHAR(100) NOT NULL,
    CONSTRAINT uq_permission_role_action UNIQUE (nom_role, action_autorisee)
);

-- ---------------------------------------------------------------------------
-- ReconnaissanceFaciale — empreinte de référence (embedding FaceNet)
-- ---------------------------------------------------------------------------
CREATE TABLE reconnaissances_faciales (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    utilisateur_id      INT NOT NULL UNIQUE,
    empreinte_faciale   NVARCHAR(MAX) NOT NULL,   -- JSON du vecteur d'embedding
    modele              NVARCHAR(50) DEFAULT 'Facenet',
    date_enregistrement DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT fk_empreinte_utilisateur FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- Configuration — seuils globaux (ligne unique, id = 1)
-- ---------------------------------------------------------------------------
CREATE TABLE configuration (
    id                      INT PRIMARY KEY,
    seuil_min               FLOAT NOT NULL DEFAULT 0.45 CHECK (seuil_min BETWEEN 0 AND 1),
    seuil_max               FLOAT NOT NULL DEFAULT 0.75 CHECK (seuil_max BETWEEN 0 AND 1),
    seuil_distance          FLOAT NOT NULL DEFAULT 1.0 CHECK (seuil_distance > 0),
    modele_reconnaissance   NVARCHAR(50) DEFAULT 'Facenet',
    date_maj                DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    maj_par_id              INT NULL,
    CONSTRAINT ck_config_seuils CHECK (seuil_min < seuil_max),
    CONSTRAINT fk_config_admin FOREIGN KEY (maj_par_id) REFERENCES administrateurs(id)
);

-- ---------------------------------------------------------------------------
-- Pointage
-- ---------------------------------------------------------------------------
CREATE TABLE pointages (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    utilisateur_id      INT NOT NULL,
    date_heure          DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    type                NVARCHAR(20) DEFAULT 'ENTREE',
    mode                BIT NOT NULL DEFAULT 0,             -- 1 = Télétravail, 0 = Présentiel
    methode_validation  NVARCHAR(30) NULL,
    statut              NVARCHAR(20) NOT NULL
                            CONSTRAINT ck_pointage_statut CHECK (statut IN ('VALIDE','EN_ATTENTE','REJETE')),
    score_confiance     FLOAT NULL,
    photo_capture       NVARCHAR(255) NULL,
    CONSTRAINT fk_pointage_utilisateur FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
);
CREATE INDEX ix_pointages_utilisateur_date ON pointages(utilisateur_id, date_heure DESC);
CREATE INDEX ix_pointages_date ON pointages(date_heure);

-- ---------------------------------------------------------------------------
-- Teletravail
-- ---------------------------------------------------------------------------
CREATE TABLE teletravail (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    utilisateur_id      INT NOT NULL,
    date_debut          DATE NOT NULL,
    date_fin            DATE NOT NULL,
    motif               NVARCHAR(255) NULL,
    statut              NVARCHAR(20) NOT NULL DEFAULT 'SOUMISE'
                            CONSTRAINT ck_teletravail_statut CHECK (statut IN ('SOUMISE','APPROUVE','REJETE')),
    validateur_id       INT NULL,
    date_decision       DATETIME2 NULL,
    commentaire         NVARCHAR(255) NULL,
    CONSTRAINT fk_teletravail_employe FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id),
    CONSTRAINT fk_teletravail_validateur FOREIGN KEY (validateur_id) REFERENCES utilisateurs(id),
    CONSTRAINT ck_teletravail_periode CHECK (date_fin >= date_debut)
);

-- ---------------------------------------------------------------------------
-- Conge — demandes de congé employé
-- ---------------------------------------------------------------------------
CREATE TABLE conges (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    utilisateur_id      INT NOT NULL,
    date_debut          DATE NOT NULL,
    date_fin            DATE NOT NULL,
    motif               NVARCHAR(255) NULL,
    statut              NVARCHAR(20) NOT NULL DEFAULT 'SOUMISE'
                            CONSTRAINT ck_conge_statut CHECK (statut IN ('SOUMISE','APPROUVE','REJETE')),
    validateur_id       INT NULL,
    date_decision       DATETIME2 NULL,
    commentaire         NVARCHAR(255) NULL,
    CONSTRAINT fk_conge_employe FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id),
    CONSTRAINT fk_conge_validateur FOREIGN KEY (validateur_id) REFERENCES utilisateurs(id),
    CONSTRAINT ck_conge_periode CHECK (date_fin >= date_debut)
);
CREATE INDEX ix_conges_utilisateur_periode ON conges(utilisateur_id, date_debut, date_fin);

-- ---------------------------------------------------------------------------
-- Rapport («Contrainte» : uniquement si role == 'rh', imposé côté application)
-- ---------------------------------------------------------------------------
CREATE TABLE rapports (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    type                NVARCHAR(50) NOT NULL,
    date_debut          DATE NULL,
    date_fin            DATE NULL,
    date_generation     DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    format              NVARCHAR(10) DEFAULT 'CSV',
    genere_par_id       INT NOT NULL,
    CONSTRAINT fk_rapport_utilisateur FOREIGN KEY (genere_par_id) REFERENCES utilisateurs(id)
);

GO
PRINT 'Schéma EMPREINTE créé avec succès.';
