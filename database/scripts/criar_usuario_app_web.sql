/*
  Cria o usuário de banco exclusivo do app web (contained user no Azure SQL),
  com o mínimo de permissões necessárias.

  Rode CONECTADO AO BANCO DA APLICAÇÃO (não ao master), depois da migração 001.
  Troque a senha por uma senha forte e guarde-a apenas no secret DATABASE_URL
  do Container Apps / no seu .env local. Nunca a coloque no repositório.
*/

CREATE USER app_web WITH PASSWORD = '<SENHA_FORTE_AQUI>';
GO

-- Leitura dos dados do sistema
GRANT SELECT ON dbo.LeiturasSensores TO app_web;
GRANT SELECT ON dbo.Estufas         TO app_web;
GRANT SELECT ON dbo.Deteccoes       TO app_web;
GRANT SELECT ON dbo.Dispositivos    TO app_web;

-- Gestão de usuários e permissões (somente pelo ADM, validado na API)
GRANT SELECT, INSERT, UPDATE ON dbo.Usuarios      TO app_web;
GRANT SELECT, INSERT, DELETE ON dbo.UsuarioEstufa TO app_web;
GO
