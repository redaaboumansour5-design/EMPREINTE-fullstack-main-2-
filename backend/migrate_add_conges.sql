-- Migration : table conges (demandes de congé employé)
-- Exécution : sqlcmd -S localhost\SQLEXPRESS -d EmpreintePointage -U sa -P *** -i migrate_add_conges.sql

IF OBJECT_ID('conges', 'U') IS NULL
BEGIN
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
    PRINT 'Table conges créée.';
END
ELSE
    PRINT 'Table conges déjà existante — aucune action.';
GO
