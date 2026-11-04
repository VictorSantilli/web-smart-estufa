/*
  Réplica do esquema ATUAL do Azure SQL (levantado em 04/11/2026 a partir de
  sys.tables, sys.columns, sys.foreign_keys e sys.indexes).

  USO: somente para criar um banco LOCAL de desenvolvimento/testes (docker-compose).
  NÃO execute no Azure: as tabelas já existem lá.

  Observações:
  - As colunas dos índices não clusterizados não vieram no levantamento; as
    colunas abaixo são presumidas pelo nome do índice.
  - As restrições CHECK de Deteccoes seguem o Apêndice A do TCC.
*/

CREATE TABLE Usuarios (
    Id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Usuarios PRIMARY KEY,
    Email VARCHAR(255) NOT NULL,
    Nome VARCHAR(255) NULL,
    SenhaHash VARCHAR(255) NOT NULL,
    DataCriacao DATETIME2 NOT NULL,
    Adm BIT NOT NULL,
    PushToken NVARCHAR(255) NULL,
    CONSTRAINT UQ_Usuarios_Email UNIQUE (Email)
);
GO

CREATE TABLE Estufas (
    Id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Estufas PRIMARY KEY,
    NomeEstufa VARCHAR(100) NULL,
    DataCriacao DATETIME NULL
);
GO

CREATE TABLE UsuarioEstufa (
    UsuarioId INT NOT NULL,
    EstufaId INT NOT NULL,
    DataVinculo DATE NOT NULL,
    CONSTRAINT FK_UE_Usuario FOREIGN KEY (UsuarioId) REFERENCES Usuarios(Id),
    CONSTRAINT FK_UE_Estufa FOREIGN KEY (EstufaId) REFERENCES Estufas(Id)
);
GO

CREATE TABLE LeiturasSensores (
    Id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    DeviceId VARCHAR(50) NOT NULL,
    Temperatura DECIMAL(5,2) NULL,
    Umidade DECIMAL(5,2) NULL,
    DataHoraEnvio DATETIME2 NOT NULL,
    DataHoraGravacao DATETIME2 NULL
        DEFAULT (CONVERT([datetime2],((sysutcdatetime() AT TIME ZONE 'UTC') AT TIME ZONE 'E. South America Standard Time'))),
    TempTeto DECIMAL(5,2) NULL,
    UmidTeto DECIMAL(5,2) NULL,
    IdEstufa INT NULL,
    Ventoinhas BIT NULL,
    CONSTRAINT FK_Leituras_Estufa FOREIGN KEY (IdEstufa) REFERENCES Estufas(Id)
);
GO

CREATE NONCLUSTERED INDEX IX_Leituras_DeviceId_DataHora
    ON LeiturasSensores (DeviceId, DataHoraEnvio);
GO

CREATE TABLE Deteccoes (
    Id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Deteccoes PRIMARY KEY,
    EstufaId INT NULL,
    ImagemBlob VARCHAR(400) NOT NULL,
    Classe VARCHAR(20) NOT NULL,
    Confianca DECIMAL(7,6) NOT NULL,
    ProbBacteriano DECIMAL(7,6) NULL,
    ProbFungico DECIMAL(7,6) NULL,
    ProbSaudavel DECIMAL(7,6) NULL,
    PatogenoDetectado BIT NOT NULL,
    Alerta BIT NOT NULL,
    ModeloVersao VARCHAR(100) NOT NULL,
    TempoInferenciaMs DECIMAL(9,3) NOT NULL,
    DataHoraDeteccao DATETIME2(3) NOT NULL,
    DataHoraGravacao DATETIME2(3) NOT NULL
        DEFAULT (CONVERT([datetime2],((sysutcdatetime() AT TIME ZONE 'UTC') AT TIME ZONE 'E. South America Standard Time'))),
    BboxX REAL NULL,
    BboxY REAL NULL,
    BboxW REAL NULL,
    BboxH REAL NULL,
    HeatmapBlob VARCHAR(400) NULL,
    Lido BIT NULL,
    Resolvido BIT NULL,
    ProbAlface DECIMAL(7,6) NULL,
    ModeloDominioVersao VARCHAR(100) NULL,
    TempoVerificacaoMs DECIMAL(9,3) NULL,
    CONSTRAINT CK_Deteccoes_Classe CHECK (Classe IN ('fungico', 'bacteriano', 'saudavel')),
    CONSTRAINT CK_Deteccoes_Confianca CHECK (Confianca >= 0 AND Confianca <= 1),
    CONSTRAINT CK_Deteccoes_PatogenoCoerente
        CHECK (PatogenoDetectado = CASE WHEN Classe = 'saudavel' THEN 0 ELSE 1 END),
    CONSTRAINT CK_Deteccoes_AlertaExigePatogeno CHECK (Alerta = 0 OR PatogenoDetectado = 1),
    CONSTRAINT CK_Deteccoes_Tempo CHECK (TempoInferenciaMs >= 0),
    CONSTRAINT UQ_Deteccoes_ImagemBlob UNIQUE (ImagemBlob),
    CONSTRAINT FK_Deteccoes_Estufa FOREIGN KEY (EstufaId) REFERENCES Estufas(Id)
);
GO

CREATE NONCLUSTERED INDEX IX_Deteccoes_Estufa_Data ON Deteccoes (EstufaId, DataHoraDeteccao);
GO
CREATE NONCLUSTERED INDEX IX_Deteccoes_Alertas ON Deteccoes (EstufaId, Alerta, Lido);
GO
