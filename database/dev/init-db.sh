#!/bin/sh
# Cria o banco LOCAL de desenvolvimento: esquema atual + migração 001 + dados fictícios.
# Executado pelo serviço "db-init" do docker-compose. Idempotente.
set -e

SQL="sqlcmd -S db -U sa -P $MSSQL_SA_PASSWORD -C -b"

echo "Aguardando o SQL Server..."
until $SQL -Q "SELECT 1" > /dev/null 2>&1; do sleep 2; done

if [ "$($SQL -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM sys.databases WHERE name = '$DB_NAME'")" = "1" ]; then
  echo "Banco $DB_NAME já existe. Nada a fazer."
  exit 0
fi

$SQL -Q "CREATE DATABASE [$DB_NAME]"
$SQL -d "$DB_NAME" -i /database/schema/000_schema_atual.sql
$SQL -d "$DB_NAME" -i /database/migrations/001_web_app.sql
$SQL -d "$DB_NAME" -i /database/dev/seed_dev.sql
echo "Banco $DB_NAME criado."
