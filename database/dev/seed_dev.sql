/*
  Dados FICTÍCIOS para o banco LOCAL de desenvolvimento (docker-compose).
  Não execute no Azure.

  Cria 2 estufas, 1 dispositivo por estufa e ~65 dias de leituras a cada 5 min,
  com algumas lacunas, leituras nulas (sensor com falha), uma duplicata e
  leituras com IdEstufa nulo, para exercitar as regras de negócio.
*/

SET NOCOUNT ON;

INSERT INTO Estufas (NomeEstufa, DataCriacao) VALUES
    ('Estufa 01', GETDATE()),
    ('Estufa 02', GETDATE());

INSERT INTO Dispositivos (DeviceId, EstufaId, Descricao) VALUES
    ('esp32-dev-01', 1, 'ESP32 de desenvolvimento - Estufa 01'),
    ('esp32-dev-02', 2, 'ESP32 de desenvolvimento - Estufa 02');

DECLARE @agora DATETIME2 = DATEADD(SECOND, -DATEPART(SECOND, SYSUTCDATETIME()), SYSUTCDATETIME());
DECLARE @t DATETIME2 = DATEADD(DAY, -65, @agora);
DECLARE @i INT = 0;
DECLARE @hora FLOAT, @temp FLOAT, @umid FLOAT;

WHILE @t <= @agora
BEGIN
    -- Ciclo diário: mais quente às 15h (UTC-3 -> 18h UTC)
    SET @hora = DATEPART(HOUR, @t) + DATEPART(MINUTE, @t) / 60.0;
    SET @temp = 21 + 5 * SIN((@hora - 12) * PI() / 12) + (RAND(CHECKSUM(NEWID())) - 0.5) * 1.5;
    SET @umid = 75 - 10 * SIN((@hora - 12) * PI() / 12) + (RAND(CHECKSUM(NEWID())) - 0.5) * 4;

    -- Lacuna de 6 h há 10 dias (sem leituras)
    IF NOT (@t BETWEEN DATEADD(DAY, -10, @agora) AND DATEADD(HOUR, 6, DATEADD(DAY, -10, @agora)))
    BEGIN
        INSERT INTO LeiturasSensores
            (DeviceId, Temperatura, Umidade, DataHoraEnvio, TempTeto, UmidTeto, IdEstufa, Ventoinhas)
        VALUES (
            'esp32-dev-01',
            CASE WHEN @i % 97 = 0 THEN NULL ELSE ROUND(@temp, 0) END,   -- falha ocasional do dossel
            CASE WHEN @i % 97 = 0 THEN NULL ELSE ROUND(@umid, 0) END,
            @t,
            ROUND(@temp + 1.8, 0),
            ROUND(@umid - 5, 0),
            CASE WHEN @i % 200 = 0 THEN NULL ELSE 1 END,                -- IdEstufa nulo às vezes
            CASE WHEN @temp + 1.8 > 24 THEN 1 ELSE 0 END
        );

        INSERT INTO LeiturasSensores
            (DeviceId, Temperatura, Umidade, DataHoraEnvio, TempTeto, UmidTeto, IdEstufa, Ventoinhas)
        VALUES ('esp32-dev-02', ROUND(@temp - 1, 0), ROUND(@umid + 3, 0), @t,
                ROUND(@temp + 0.5, 0), ROUND(@umid, 0), 2, NULL);
    END

    SET @t = DATEADD(MINUTE, 5, @t);
    SET @i += 1;
END

-- Uma leitura duplicada (mesmo DeviceId e DataHoraEnvio), como observado no TCC
INSERT INTO LeiturasSensores (DeviceId, Temperatura, Umidade, DataHoraEnvio, TempTeto, UmidTeto, IdEstufa)
SELECT TOP 1 DeviceId, Temperatura, Umidade, DataHoraEnvio, TempTeto, UmidTeto, IdEstufa
FROM LeiturasSensores WHERE DeviceId = 'esp32-dev-01' ORDER BY DataHoraEnvio DESC;

PRINT 'Seed de desenvolvimento concluido.';
