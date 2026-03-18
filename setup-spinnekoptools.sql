-- =============================================================================
-- SpinnekopTools database setup
-- =============================================================================
-- Eenmalig uitvoeren als sa of sysadmin in SSMS op 10.0.1.5\RIDDERIQ
--
-- Wat dit doet:
--   1. Maakt de SpinnekopTools database aan (audit logs, los van RidderIQ)
--   2. Maakt de BOM_IMPORT_LOG tabel aan
--   3. Geeft ridderadmin INSERT + SELECT rechten
-- =============================================================================

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'SpinnekopTools')
    CREATE DATABASE SpinnekopTools;
GO

USE SpinnekopTools;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'BOM_IMPORT_LOG')
CREATE TABLE BOM_IMPORT_LOG (
    id                  INT IDENTITY PRIMARY KEY,
    tijdstip            DATETIME2        NOT NULL,
    gebruiker           NVARCHAR(100)    NOT NULL,
    toestel             NVARCHAR(100)    NOT NULL,
    omgeving            NVARCHAR(50)     NOT NULL,
    database_naam       NVARCHAR(200)    NOT NULL DEFAULT '',
    excel_bestand       NVARCHAR(500),
    bovenste_artikel    NVARCHAR(100),
    stap                NVARCHAR(50)     NOT NULL,
    status              NVARCHAR(20)     NOT NULL,
    artikelen           INT,
    stuklijsten         INT,
    zaagregels          INT,
    fouten_json         NVARCHAR(MAX),
    waarschuwingen      INT,
    csv_files           NVARCHAR(MAX),
    output_map          NVARCHAR(500),
    kmb_artikelen       INT,
    kmb_substuklijsten  INT,
    kmb_overgeslagen    INT,
    kmb_fouten          NVARCHAR(MAX)
);
GO

-- Rechten voor ridderadmin
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'ridderadmin')
    CREATE USER ridderadmin FOR LOGIN ridderadmin;

GRANT INSERT, SELECT ON BOM_IMPORT_LOG TO ridderadmin;
GO

-- Verificatie
SELECT 'Database aangemaakt' AS status, name FROM sys.databases WHERE name = 'SpinnekopTools';
SELECT 'Tabel aangemaakt' AS status, name FROM sys.tables WHERE name = 'BOM_IMPORT_LOG';
SELECT 'Rechten' AS status, dp.name, p.permission_name
FROM sys.database_permissions p
JOIN sys.database_principals dp ON p.grantee_principal_id = dp.principal_id
WHERE dp.name = 'ridderadmin';
GO
