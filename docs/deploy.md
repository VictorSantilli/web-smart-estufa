# Deploy no Azure Container Apps

Guia para colocar o Smart Estufa Web em produção. O deploy em si é automático (GitHub Actions);
os passos abaixo são a preparação feita **uma vez**.

```
GitHub Actions ──(OIDC)──► Azure
   │ build da imagem            ├─ Container Registry (imagens)
   │                            ├─ Container Apps (FastAPI + React, HTTPS)
   └─ deploy (infra/main.bicep) ├─ Log Analytics + Application Insights
                                └─ Azure SQL existente (não é criado nem alterado pelo deploy)
```

## 1. Banco de dados (Azure SQL existente)

Faça no Query Editor do portal ou no Azure Data Studio, conectado ao banco da aplicação.

1. **Migração 001**: leia e execute `database/migrations/001_web_app.sql`. Ela é idempotente e roda
   em transação (adiciona colunas com valor padrão em `Usuarios`, a PK de `UsuarioEstufa`, um
   índice em `LeiturasSensores` e a tabela `Dispositivos`). Reversão:
   `001_web_app_rollback.sql`.
2. **Usuário do app web**: troque a senha em `database/scripts/criar_usuario_app_web.sql` (só na
   sua cópia, não faça commit) e execute. O app usa esse usuário, com permissões mínimas, e não o
   administrador do servidor.
3. **Dispositivo**: cadastre o ESP32 para que as leituras gravadas com `IdEstufa` nulo sejam
   atribuídas à estufa:
   ```sql
   SELECT DISTINCT DeviceId FROM dbo.LeiturasSensores;           -- descubra o DeviceId
   INSERT INTO dbo.Dispositivos (DeviceId, EstufaId, Descricao)
   VALUES ('<DeviceId>', 1, 'ESP32 com DHT22 no dossel e no teto');
   ```
4. **Firewall do servidor SQL**: em *Rede*, marque **"Permitir que serviços e recursos do Azure
   acessem este servidor"**. O Container Apps no plano de consumo não tem IP de saída fixo.

`DATABASE_URL` (senha com caracteres especiais deve ser codificada para URL, ex.: `@` → `%40`):

```
mssql+pyodbc://app_web:<senha>@<servidor>.database.windows.net:1433/<banco>?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
```

## 2. Azure: resource group e acesso do GitHub (OIDC)

Rode no **Azure Cloud Shell** (ícone `>_` no portal, modo Bash), que já vem com a CLI e logado.
Use a **mesma região do Azure SQL** para menor latência
(`az sql server list --query "[].{servidor:name, regiao:location}" -o table`).

O GitHub entra no Azure com uma **identidade gerenciada** com credencial federada (OIDC): não há
senha guardada no GitHub e não é preciso permissão para criar aplicativos no Entra ID (contas de
estudante normalmente não têm).

```bash
RG=rg-smart-estufa-web
LOCATION=canadacentral          # região do seu Azure SQL
REPO=VictorSantilli/web-smart-estufa
SUB=$(az account show --query id -o tsv)

az group create -n $RG -l $LOCATION -o none

# Assinaturas novas vêm com estes serviços desabilitados (erro MissingSubscriptionRegistration)
for ns in Microsoft.App Microsoft.ContainerRegistry Microsoft.OperationalInsights Microsoft.Insights Microsoft.ManagedIdentity; do
  az provider register --namespace $ns --wait
done

az identity create -g $RG -n smart-estufa-github -l $LOCATION -o none
CLIENT_ID=$(az identity show -g $RG -n smart-estufa-github --query clientId -o tsv)
PRINCIPAL_ID=$(az identity show -g $RG -n smart-estufa-github --query principalId -o tsv)

# Confia apenas em execuções do ambiente "production" deste repositório
az identity federated-credential create -g $RG --identity-name smart-estufa-github -n github-production \
  --issuer https://token.actions.githubusercontent.com \
  --subject "repo:$REPO:environment:production" \
  --audiences api://AzureADTokenExchange -o none

# Permissões apenas neste resource group.
# O segundo papel é necessário para o Bicep dar ao Container App o acesso ao registro de imagens.
az role assignment create --assignee-object-id $PRINCIPAL_ID --assignee-principal-type ServicePrincipal \
  --role Contributor --scope /subscriptions/$SUB/resourceGroups/$RG -o none
az role assignment create --assignee-object-id $PRINCIPAL_ID --assignee-principal-type ServicePrincipal \
  --role "Role Based Access Control Administrator" --scope /subscriptions/$SUB/resourceGroups/$RG -o none

echo "AZURE_CLIENT_ID=$CLIENT_ID"
echo "AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)"
echo "AZURE_SUBSCRIPTION_ID=$SUB"
```

> **Se o login falhar com `AADSTS700213: No matching federated identity record`:** o GitHub pode enviar o
> subject com os IDs numéricos do dono e do repositório (ex.: `repo:VictorSantilli@130602837/web-smart-estufa@1444968785:environment:production`).
> Copie o valor de "subject claim" do log do passo *Login no Azure* e crie uma credencial com ele:
>
> ```bash
> az identity federated-credential create -g rg-smart-estufa-web --identity-name smart-estufa-github -n github-production-v2 \
>   --issuer https://token.actions.githubusercontent.com \
>   --subject "<subject claim do log>" --audiences api://AzureADTokenExchange
> ```

## 3. GitHub: ambiente "production"

Em *Settings → Environments → New environment* crie **production** e cadastre:

| Tipo | Nome | Valor |
|---|---|---|
| Secret | `AZURE_CLIENT_ID` | saída do passo 2 |
| Secret | `AZURE_TENANT_ID` | saída do passo 2 |
| Secret | `AZURE_SUBSCRIPTION_ID` | saída do passo 2 |
| Secret | `DATABASE_URL` | URL do passo 1, com o usuário `app_web` |
| Secret | `JWT_SECRET` | gere com `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| Variable | `AZURE_RESOURCE_GROUP` | `rg-smart-estufa-web` |
| Variable | `MIN_REPLICAS` (opcional) | `0` (padrão) ou `1` |

Opcional: em *Required reviewers*, coloque você mesmo para aprovar cada deploy.

## 4. Deploy

*Actions → Deploy → Run workflow*. O workflow:

1. cria ou atualiza a infraestrutura (`infra/main.bicep`);
2. constrói a imagem (React + FastAPI) e envia ao Container Registry com a tag do commit;
3. atualiza o Container App com a imagem nova e os secrets;
4. confere `/api/health/live` e `/api/health` (este último testa a conexão com o banco).

O endereço aparece no resumo da execução (`https://smart-estufa-web.<...>.azurecontainerapps.io`).
Para voltar a uma versão anterior, rode o workflow a partir do commit desejado.

## 5. Primeiro acesso

Usuários do app mobile com `Adm = 1` já conseguem entrar (as senhas bcrypt são compatíveis).
Para criar ou promover um administrador direto no container, abra um shell nele:

```bash
az containerapp exec -g rg-smart-estufa-web -n smart-estufa-web --command sh
```

e, dentro do container (o código fica em `/app`):

```bash
cd /app && python -m app.cli create-admin --email voce@exemplo.com --name Victor
exit
```

## 6. Conferências após o primeiro deploy

- **Login, Dashboard e Histórico** com os dados reais.
- **Application Insights** (`smart-estufa-insights`): em *Live metrics* aparecem as requisições;
  em *Failures*, as exceções.
- **Limite de login por IP** (`TRUSTED_PROXY_HOPS=1`): erre a senha de um e-mail inexistente 11
  vezes seguidas; a 11ª deve responder "Muitas tentativas". Logo depois, pelo celular em outra rede,
  o login deve funcionar normalmente.
- **Logs do container**: *Container App → Monitoring → Log stream*.

## Custos (aproximados, confira na calculadora do Azure)

- **Container Apps (consumo)**: com `MIN_REPLICAS=0` o uso de um TCC costuma ficar dentro da cota
  gratuita mensal. O primeiro acesso depois de um tempo parado demora alguns segundos (o container
  liga sob demanda). Com `1`, responde sempre rápido, com custo mensal pequeno.
- **Container Registry Basic**: valor fixo mensal baixo.
- **Log Analytics / Application Insights**: por volume de dados; pequeno para este uso
  (retenção de 30 dias).
