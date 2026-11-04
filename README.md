# Smart Estufa — Aplicação Web

Aplicação web para monitoramento das estufas do projeto **Smart Estufa** (TCC): dashboard de
temperatura e umidade, histórico com máxima, média e mínima por dia, e controle de acesso por
usuário e por estufa.

O app web é um **novo cliente do Azure SQL já existente**. Ele não cria estrutura paralela: os
dados continuam sendo gravados pelas Azure Functions (telemetria do ESP32 e visão computacional),
e o app mobile segue funcionando com o mesmo banco.

## Stack

| Camada | Tecnologias |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Axios, Recharts, lucide-react |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, pyodbc (ODBC Driver 18) |
| Banco | Azure SQL Database (SQL Server) existente |
| Infra | Docker, Azure Container Apps |

## Arquitetura

Monólito modular: **um único container** em que o FastAPI atende a API em `/api` e também serve o
build do React. Frontend e API ficam na mesma origem (sem CORS em produção).

```
web-smart-estufa/
├── frontend/                 React + Vite
│   └── src/
│       ├── components/       componentes reutilizáveis (ui/ = base visual)
│       ├── pages/            telas
│       ├── layouts/          layout com sidebar e cabeçalho
│       ├── hooks/            hooks de dados (TanStack Query)
│       ├── services/         cliente HTTP e chamadas à API
│       ├── contexts/         contexto de autenticação (Etapa 3)
│       ├── routes/           rotas e guards
│       ├── types/            tipos das respostas da API
│       └── utils/            datas (UTC -> America/Sao_Paulo), helpers
├── backend/
│   ├── app/
│   │   ├── api/routes/       endpoints HTTP (validação com Pydantic)
│   │   ├── core/             configuração, erros padronizados, segurança
│   │   ├── models/           SQLAlchemy mapeando as tabelas EXISTENTES
│   │   ├── schemas/          modelos Pydantic de entrada/saída
│   │   ├── services/         regras de negócio
│   │   ├── repositories/     consultas ao banco
│   │   ├── database/         engine e sessão
│   │   └── main.py
│   └── tests/
├── database/
│   ├── schema/               réplica do esquema atual (só para banco local)
│   ├── migrations/           alterações aprovadas, aplicadas manualmente no Azure
│   ├── scripts/              usuário de banco do app (app_web)
│   └── dev/                  dados fictícios e script de criação do banco local
├── infrastructure/azure/     preparação para implantação
├── Dockerfile                imagem de produção (frontend + backend)
├── docker-compose.yml        ambiente de desenvolvimento
└── .env.example
```

Decisões e regras de negócio completas: documento *Smart Estufa Web — Proposta de arquitetura*.

## Banco de dados

O app **nunca** cria ou altera tabelas sozinho (`create_all` não é usado). As alterações aprovadas
estão em `database/migrations/` e são aplicadas manualmente:

1. `database/migrations/001_web_app.sql` — colunas `Ativo`, `TentativasFalhas`, `BloqueadoAte` e
   `TokenVersao` em `Usuarios`; PK em `UsuarioEstufa`; índice de histórico em `LeiturasSensores`;
   tabela `Dispositivos`. Idempotente e transacional. Reversão: `001_web_app_rollback.sql`.
2. `database/scripts/criar_usuario_app_web.sql` — usuário `app_web` com permissões mínimas.
3. Cadastrar o ESP32 em `Dispositivos` (instrução no final do script 001).

> O backend espera que a migração 001 tenha sido aplicada no banco usado.

## Como executar

### Opção 1 — Docker (recomendado)

Requer Docker Desktop. Sobe SQL Server local com dados fictícios, backend e frontend.

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000/api/health
- Swagger: http://localhost:8000/api/docs

O primeiro `up` leva alguns minutos (download do SQL Server e geração de ~65 dias de leituras).
Para recriar o banco local do zero: `docker compose down -v`.

Crie o primeiro administrador do banco local (a senha é pedida no terminal):

```bash
docker compose exec backend python -m app.cli create-admin --email admin@estufa.com --name "Administrador"
```

### Opção 2 — Sem Docker

Requer Python 3.12+, Node 22+ e o [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server).

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp ../.env.example .env        # ajuste DATABASE_URL (ex.: Azure SQL)
uvicorn app.main:app --reload  # http://localhost:8000
python -m app.cli create-admin --email voce@exemplo.com --name "Seu Nome"   # se precisar de um ADM

# Frontend (outro terminal)
cd frontend
npm install
npm run dev                    # http://localhost:5173 (encaminha /api para :8000)
```

### Imagem de produção

```bash
docker build -t smart-estufa-web .
docker run -p 8000:8000 --env-file .env -e APP_ENV=production smart-estufa-web
# http://localhost:8000 serve o React e a API
```

## Autenticação e permissões

- Login com e-mail e senha em `POST /api/auth/login`. O **access token** (JWT, 15 min) volta no
  corpo e fica só na memória do navegador. O **refresh token** (7 dias) vai num cookie
  `HttpOnly`, `SameSite=Strict`, restrito a `/api/auth`, e é trocado a cada renovação.
- Os tokens carregam `Usuarios.TokenVersao`: desativar o usuário, trocar a senha ou mudar o
  perfil derruba todas as sessões dele na hora.
- 5 senhas erradas bloqueiam a conta por 15 minutos (`TentativasFalhas`/`BloqueadoAte`), além de
  um limite de 10 tentativas por minuto por IP. A mensagem de erro é sempre genérica.
- Senhas: bcrypt por padrão (compatível com o app mobile). Com `PASSWORD_HASH_SCHEME=argon2id`,
  novas senhas usam Argon2id e hashes bcrypt são regravados no próximo login.
- **Perfis**: ADM (`Usuarios.Adm = 1`) gerencia usuários e vê todas as estufas; usuário comum vê
  só as estufas vinculadas em `UsuarioEstufa`.
- **Toda checagem é no backend** (`app/api/deps.py`). Estufa sem permissão responde 404, igual a
  uma estufa inexistente, para não revelar o que existe.

## Testes e qualidade

```bash
cd backend && pytest && ruff check . && ruff format --check .
cd frontend && npm run lint && npm run test && npm run build
```

## Variáveis de ambiente

Todas documentadas em `.env.example`. Nenhuma credencial fica no código; em produção, `DATABASE_URL`
e `JWT_SECRET` ficam como secrets do Container Apps.

## Etapas

- [x] 1. Análise e planejamento
- [x] 2. Estrutura inicial
- [x] 3. Autenticação e autorização
- [ ] 4. Dashboard
- [ ] 5. Histórico
- [ ] 6. Testes e segurança
- [ ] 7. Preparação para produção
