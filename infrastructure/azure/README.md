# Infraestrutura Azure

Preparação para implantação (detalhada na **Etapa 7**). Nenhum recurso é criado por enquanto.

## Alvo

| Recurso | Uso |
| --- | --- |
| Azure Container Apps | Um container com a API FastAPI + o build do React (`Dockerfile` na raiz) |
| Azure Container Registry | Armazena a imagem `smart-estufa-web` |
| Azure SQL Database | Banco **existente** (usuário `app_web`, ver `database/scripts/`) |
| Secrets do Container Apps / Key Vault | `DATABASE_URL`, `JWT_SECRET` |
| Application Insights | Monitoramento (opcional) |
| Blob Storage | Imagens das detecções (fase futura, via links SAS) |

## Pontos já preparados no código

- Toda configuração vem de variáveis de ambiente (`.env.example`).
- `APP_ENV=production` recusa subir com `JWT_SECRET` fraco ou banco SQLite.
- HTTPS terminado pelo Container Apps; o Uvicorn usa `--proxy-headers`.
- HSTS e cabeçalhos de segurança ativos em produção.
- Health check em `/api/health` (devolve 503 se o banco estiver inacessível).
- Container roda com usuário sem privilégios.

## Pendências para a Etapa 7

- Templates Bicep (Container App, ACR, secrets).
- Liberar o IP de saída do Container Apps no firewall do Azure SQL.
- Pipeline de build e deploy (GitHub Actions).
