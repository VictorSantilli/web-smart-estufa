/* Reverte a migração 001_web_app.sql. Remove as colunas/tabela criadas (e seus dados). */

SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF OBJECT_ID('dbo.Dispositivos', 'U') IS NOT NULL DROP TABLE dbo.Dispositivos;

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Leituras_Estufa_DataHoraEnvio'
           AND object_id = OBJECT_ID('dbo.LeiturasSensores'))
    DROP INDEX IX_Leituras_Estufa_DataHoraEnvio ON dbo.LeiturasSensores;

IF OBJECT_ID('dbo.PK_UsuarioEstufa', 'PK') IS NOT NULL
    ALTER TABLE dbo.UsuarioEstufa DROP CONSTRAINT PK_UsuarioEstufa;

IF COL_LENGTH('dbo.Usuarios', 'TokenVersao') IS NOT NULL
BEGIN
    ALTER TABLE dbo.Usuarios DROP CONSTRAINT DF_Usuarios_TokenVersao;
    ALTER TABLE dbo.Usuarios DROP COLUMN TokenVersao;
END

IF COL_LENGTH('dbo.Usuarios', 'BloqueadoAte') IS NOT NULL
    ALTER TABLE dbo.Usuarios DROP COLUMN BloqueadoAte;

IF COL_LENGTH('dbo.Usuarios', 'TentativasFalhas') IS NOT NULL
BEGIN
    ALTER TABLE dbo.Usuarios DROP CONSTRAINT DF_Usuarios_TentativasFalhas;
    ALTER TABLE dbo.Usuarios DROP COLUMN TentativasFalhas;
END

IF COL_LENGTH('dbo.Usuarios', 'Ativo') IS NOT NULL
BEGIN
    ALTER TABLE dbo.Usuarios DROP CONSTRAINT DF_Usuarios_Ativo;
    ALTER TABLE dbo.Usuarios DROP COLUMN Ativo;
END

COMMIT TRANSACTION;
