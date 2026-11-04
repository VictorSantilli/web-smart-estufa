/*
  Migração 001 — alterações aprovadas para o app web Smart Estufa (04/11/2026).

  O QUE FAZ
    1. Usuarios.Ativo             -> desativar usuário
    2. PK em UsuarioEstufa        -> impede vínculos duplicados
    3. Índice (IdEstufa, DataHoraEnvio) em LeiturasSensores -> histórico rápido
    4. Usuarios.TentativasFalhas e BloqueadoAte -> limite de tentativas de login
    5. Tabela Dispositivos        -> vínculo DeviceId -> estufa
    6. Usuarios.TokenVersao       -> invalida sessões ao desativar/trocar senha

  COMPATIBILIDADE
    Todas as colunas novas têm DEFAULT; o app mobile e as Azure Functions
    continuam funcionando sem alteração.

  COMO APLICAR
    Rode no Query editor do Azure (ou SSMS) com um usuário com permissão de DDL.
    O script é idempotente (pode ser executado mais de uma vez) e roda em transação:
    se algo falhar, nada é alterado. Reverter: 001_web_app_rollback.sql.
*/

SET XACT_ABORT ON;
BEGIN TRANSACTION;

-- Pré-verificação: vínculos duplicados impediriam a chave primária (item 2).
IF EXISTS (
    SELECT 1 FROM UsuarioEstufa GROUP BY UsuarioId, EstufaId HAVING COUNT(*) > 1
)
    THROW 50001, 'Existem vinculos duplicados em UsuarioEstufa. Remova-os antes de aplicar a migracao.', 1;

-- 1. Desativar usuário
IF COL_LENGTH('dbo.Usuarios', 'Ativo') IS NULL
    ALTER TABLE dbo.Usuarios ADD Ativo BIT NOT NULL
        CONSTRAINT DF_Usuarios_Ativo DEFAULT (1);

-- 2. Chave primária composta em UsuarioEstufa
IF NOT EXISTS (
    SELECT 1 FROM sys.key_constraints
    WHERE type = 'PK' AND parent_object_id = OBJECT_ID('dbo.UsuarioEstufa')
)
    ALTER TABLE dbo.UsuarioEstufa ADD CONSTRAINT PK_UsuarioEstufa
        PRIMARY KEY (UsuarioId, EstufaId);

-- 3. Índice para consultas de histórico por estufa
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_Leituras_Estufa_DataHoraEnvio'
      AND object_id = OBJECT_ID('dbo.LeiturasSensores')
)
    CREATE NONCLUSTERED INDEX IX_Leituras_Estufa_DataHoraEnvio
        ON dbo.LeiturasSensores (IdEstufa, DataHoraEnvio)
        INCLUDE (DeviceId, Temperatura, Umidade, TempTeto, UmidTeto, Ventoinhas, DataHoraGravacao);

-- 4. Limite de tentativas de login
IF COL_LENGTH('dbo.Usuarios', 'TentativasFalhas') IS NULL
    ALTER TABLE dbo.Usuarios ADD TentativasFalhas INT NOT NULL
        CONSTRAINT DF_Usuarios_TentativasFalhas DEFAULT (0);

IF COL_LENGTH('dbo.Usuarios', 'BloqueadoAte') IS NULL
    ALTER TABLE dbo.Usuarios ADD BloqueadoAte DATETIME2 NULL; -- UTC

-- 5. Vínculo dispositivo -> estufa
IF OBJECT_ID('dbo.Dispositivos', 'U') IS NULL
    CREATE TABLE dbo.Dispositivos (
        DeviceId VARCHAR(50) NOT NULL CONSTRAINT PK_Dispositivos PRIMARY KEY,
        EstufaId INT NOT NULL
            CONSTRAINT FK_Dispositivos_Estufa REFERENCES dbo.Estufas(Id),
        Descricao VARCHAR(100) NULL,
        Ativo BIT NOT NULL CONSTRAINT DF_Dispositivos_Ativo DEFAULT (1),
        DataCriacao DATETIME2 NOT NULL CONSTRAINT DF_Dispositivos_DataCriacao
            DEFAULT (SYSUTCDATETIME())
    );

-- 6. Versão do token (invalidação de sessões)
IF COL_LENGTH('dbo.Usuarios', 'TokenVersao') IS NULL
    ALTER TABLE dbo.Usuarios ADD TokenVersao INT NOT NULL
        CONSTRAINT DF_Usuarios_TokenVersao DEFAULT (0);

COMMIT TRANSACTION;

/*
  DEPOIS DA MIGRAÇÃO: cadastre o ESP32 (troque os valores pelo DeviceId real e
  pelo Id da estufa). Para descobrir o DeviceId:
      SELECT DeviceId, IdEstufa, COUNT(*) FROM LeiturasSensores GROUP BY DeviceId, IdEstufa;

  INSERT INTO dbo.Dispositivos (DeviceId, EstufaId, Descricao)
  VALUES ('<DeviceId>', 1, 'ESP32 com DHT22 no dossel e no teto');
*/
