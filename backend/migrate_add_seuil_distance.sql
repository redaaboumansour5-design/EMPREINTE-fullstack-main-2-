-- ============================================================================
-- Migration : Ajout de la colonne seuil_distance dans la table configuration
-- ============================================================================
-- Exécution :
--   1. Via SSMS  : Ouvrir ce fichier et exécuter (F5)
--   2. Via sqlcmd : sqlcmd -S localhost\SQLEXPRESS -d EmpreintePointage -U sa -P *** -i migrate_add_seuil_distance.sql
-- ============================================================================

USE EmpreintePointage;
GO

-- Ajout de la colonne seuil_distance
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('configuration')
    AND name = 'seuil_distance'
)
BEGIN
    ALTER TABLE configuration
    ADD seuil_distance FLOAT NOT NULL CONSTRAINT df_config_seuil_distance DEFAULT 1.0;

    -- Ajout de la contrainte CHECK (seuil_distance > 0)
    ALTER TABLE configuration
    ADD CONSTRAINT ck_config_seuil_distance CHECK (seuil_distance > 0);

    PRINT 'Colonne seuil_distance ajoutée avec succès.';
END
ELSE
    PRINT 'La colonne seuil_distance existe déjà.';
GO

