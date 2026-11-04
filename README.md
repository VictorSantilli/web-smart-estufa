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

### Produção (Azure Container Apps)

Infraestrutura em `infra/main.bicep` e deploy pelo workflow **Deploy** (manual). Passo a passo,
incluindo banco, acesso do GitHub ao Azure e secrets: **[docs/deploy.md](docs/deploy.md)**.

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

## Dashboard

`GET /api/dashboard/{estufa}` devolve os indicadores já calculados:

- **Última leitura** por `DataHoraEnvio` (UTC). Leituras com `IdEstufa` nulo entram pela tabela
  `Dispositivos` (DeviceId → estufa).
- **Última comunicação** = `MAX(DataHoraGravacao)`, convertida de Brasília para UTC (leituras da
  fila offline do ESP32 chegam com hora de medição antiga, mas contam como comunicação).
- **Online** quando a última comunicação tem até `STALE_AFTER_MINUTES` (15 min).
- **Faixas**: temperatura < 16 °C baixa · até 25 normal · > 25 atenção · > 26 crítica; umidade
  < 65 % baixa · > 85 % risco de fungos (configuráveis no `.env`).
- **Sensor com falha**: se a leitura mais recente veio nula, o card mostra o último valor válido e
  o sensor aparece como "falha".
- **Ventoinhas**: `Ventoinhas` nula = "sem informação".

Também: `GET /api/sensors/{estufa}/latest` (leitura bruta) e `GET /api/greenhouses/{estufa}/devices`.

## Histórico

`GET /api/history/{estufa}?period=24h|7d|30d` ou `?start=AAAA-MM-DD&end=AAAA-MM-DD`:

- **24h**: janela móvel das últimas 24 horas, com cada medição (`granularity = raw`).
- **7d / 30d**: últimos 7 ou 30 dias do calendário de Brasília, incluindo hoje, com mínima, média
  e máxima por dia (`granularity = daily`). O agrupamento por dia é feito no SQL Server com
  `AT TIME ZONE`, a partir de `DataHoraEnvio` (UTC).
- **Personalizado**: datas inclusivas, até `HISTORY_MAX_DAYS` (60) dias, fim não pode ser futuro.
  Até 2 dias mostra cada medição; acima disso, agregados por dia.
- Medições repetidas (mesmo `DeviceId` + `DataHoraEnvio`, reenvios da fila offline) contam uma vez.
- Valores nulos (sensor em falha) são ignorados nos agregados. Dias sem dados vêm com `samples = 0`
  e o gráfico mostra a falha; no modo bruto, intervalos maiores que 15 min interrompem a linha.

Na tela: Temperatura, Umidade ou Conjunto (dois gráficos sincronizados, um por grandeza, sem eixo
duplo), Dossel / Teto / Ambos, linhas de referência das faixas e visão em tabela. O período fica na
URL (`/historico?periodo=7d`), então dá para compartilhar o link.

## Detecções da IA

`GET /api/detections/{estufa}` lista a tabela `Deteccoes` (gravada pela Function de visão), mais
recentes primeiro, 24 por página. Filtros: `class` (saudavel, fungico, bacteriano), `start`/`end`
(dias de Brasília, inclusivos), `alert`, `status`.

- **Imagem**: `GET /api/detections/{estufa}/{id}/image` busca o blob de `ImagemBlob` na conta
  `BLOB_ACCOUNT_URL`, container `BLOB_CONTAINER`, **depois** de checar o acesso à estufa. O
  navegador baixa a imagem com o token e a exibe por uma URL local (`blob:`); o blob nunca fica
  público. URLs de outras contas gravadas no banco são recusadas.
- **Acesso ao Blob**: identidade gerenciada do Container App com o papel *Storage Blob Data Reader*
  na conta (sem chave). Conta de outro diretório: token SAS só de leitura em `BLOB_SAS_TOKEN`
  (secret); container público: `BLOB_ANONYMOUS=true`. Localmente: `az login` ou
  `BLOB_CONNECTION_STRING` (ex.: Azurite). Detalhes no passo 6 de `docs/deploy.md`.
- **Horário**: a Function grava `DataHoraDeteccao` no horário de Brasília (`DETECTION_TIME_IS_UTC=false`);
  a API devolve em UTC e a tela mostra em Brasília.
- Detecções com `EstufaId` nulo não aparecem (não há como saber a estufa).

Na tela **Detecções da IA**: grade de fotos com o resultado (Saudável, Fúngico, Bacteriano), a
confiança e o alerta; ao clicar, a foto ampliada e a probabilidade de cada classe.

## Segurança

- **Permissões só no backend**: um teste percorre todas as rotas da API e garante que nenhuma
  responde sem token (exceto health, login, refresh e logout), e que nenhuma rota com estufa
  devolve dados de estufa não autorizada.
- **Cabeçalhos**: CSP restritiva (sem scripts inline ou externos), `X-Frame-Options: DENY`,
  `nosniff`, `Permissions-Policy`, HSTS em produção e `Cache-Control: no-store` na API. O Swagger
  tem uma CSP própria que libera apenas o CDN dele.
- **Swagger** desligado por padrão em produção (`ENABLE_DOCS` liga explicitamente).
- **Limite de login por IP**: o IP vem do `X-Forwarded-For` contando `TRUSTED_PROXY_HOPS` a partir
  do fim (no Container Apps, 1). As primeiras entradas do cabeçalho podem ser forjadas pelo cliente.
- **Senhas** de 8 a 72 bytes: o bcrypt ignora o que passa de 72 bytes.
- **JWT** só com HS256/HS384/HS512; após o login, o retorno para a página anterior aceita apenas
  caminhos internos.
- **Dependências**: `pip-audit` e `npm audit` no CI (também toda segunda-feira) e Dependabot.

## Testes e qualidade

```bash
cd backend && pytest --cov && ruff check . && ruff format --check .   # cobertura mínima 95 %
cd frontend && npm run lint && npm run test:coverage && npm run build # pisos em vite.config.ts
```

## Variáveis de ambiente

Todas documentadas em `.env.example`. Nenhuma credencial fica no código; em produção, `DATABASE_URL`
e `JWT_SECRET` ficam como secrets do Container Apps.

## Etapas

- [x] 1. Análise e planejamento
- [x] 2. Estrutura inicial
- [x] 3. Autenticação e autorização
- [x] 4. Dashboard
- [x] 5. Histórico
- [x] 6. Testes e segurança
- [x] 7. Preparação para produção ([guia de deploy](docs/deploy.md))
- [x] 8. Histórico das detecções da IA
