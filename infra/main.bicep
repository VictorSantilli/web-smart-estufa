// Infraestrutura do Smart Estufa Web no Azure (resource group já existente).
//
// Cria: Log Analytics, Application Insights, Azure Container Registry, identidade
// gerenciada (AcrPull), ambiente do Container Apps e o Container App.
// O Azure SQL NÃO é criado aqui: a aplicação usa o banco que já existe.
//
// O workflow de deploy roda este arquivo duas vezes:
//   1) deployApp=false  -> garante registro/ambiente (para poder enviar a imagem)
//   2) deployApp=true   -> cria/atualiza o Container App com a imagem nova

targetScope = 'resourceGroup'

@description('Prefixo dos nomes dos recursos (letras minúsculas, números e hífen).')
@minLength(3)
@maxLength(20)
param appName string = 'smart-estufa'

@description('Região dos recursos.')
param location string = resourceGroup().location

@description('false: só a infraestrutura de apoio. true: também o Container App.')
param deployApp bool = true

@description('Imagem completa do container (ex.: <registro>.azurecr.io/smart-estufa-web:<sha>).')
param containerImage string = ''

@secure()
@description('DATABASE_URL do Azure SQL (usuário app_web). Obrigatório quando deployApp=true.')
param databaseUrl string = ''

@secure()
@description('JWT_SECRET com pelo menos 32 caracteres. Obrigatório quando deployApp=true.')
param jwtSecret string = ''

@description('URL da conta do Blob Storage com as imagens da IA (ex.: https://<conta>.blob.core.windows.net). Vazio = sem imagens.')
param blobAccountUrl string = ''

@description('Container do Blob Storage com as imagens da IA.')
param blobContainer string = ''

@secure()
@description('Token SAS só de leitura do container de imagens (quando a conta é de outro diretório). Vazio = não usa.')
param blobSasToken string = ''

@description('true quando o container de imagens tem leitura pública (sem credencial).')
param blobAnonymous bool = false

@description('Réplicas mínimas. 0 = escala a zero quando ninguém usa (primeiro acesso demora alguns segundos).')
@minValue(0)
@maxValue(3)
param minReplicas int = 0

@description('Réplicas máximas.')
@minValue(1)
@maxValue(5)
param maxReplicas int = 2

@description('Dias de retenção dos logs.')
param logRetentionDays int = 30

var suffix = uniqueString(resourceGroup().id)
var registryName = take('${replace(appName, '-', '')}${suffix}', 50)
var tags = {
  app: appName
  project: 'TCC Smart Estufa'
}
// Papel interno do Azure "AcrPull"
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${appName}-logs'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: logRetentionDays
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${appName}-insights'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false
  }
}

// Identidade do Container App para baixar imagens do registro (sem senha).
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${appName}-identity'
  location: location
  tags: tags
}

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, identity.id, acrPullRoleId)
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${appName}-env'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

var probePath = '/api/health/live'

resource app 'Microsoft.App/containerApps@2024-03-01' = if (deployApp) {
  name: '${appName}-web'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: identity.id
        }
      ]
      secrets: concat([
        { name: 'database-url', value: databaseUrl }
        { name: 'jwt-secret', value: jwtSecret }
        { name: 'appinsights-connection-string', value: appInsights.properties.ConnectionString }
      ], empty(blobSasToken) ? [] : [
        { name: 'blob-sas-token', value: blobSasToken }
      ])
    }
    template: {
      containers: [
        {
          name: 'web'
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: concat([
            { name: 'APP_ENV', value: 'production' }
            { name: 'LOG_LEVEL', value: 'INFO' }
            { name: 'WEB_CONCURRENCY', value: '2' }
            // O ingress do Container Apps acrescenta o IP real ao X-Forwarded-For.
            { name: 'TRUSTED_PROXY_HOPS', value: '1' }
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'JWT_SECRET', secretRef: 'jwt-secret' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', secretRef: 'appinsights-connection-string' }
            // Imagens da IA: identidade gerenciada (papel Storage Blob Data Reader), token SAS
            // só de leitura (secret) ou container público; ver docs/deploy.md, passo 6.
            { name: 'BLOB_ACCOUNT_URL', value: blobAccountUrl }
            { name: 'BLOB_CONTAINER', value: blobContainer }
            { name: 'AZURE_CLIENT_ID', value: identity.properties.clientId }
            { name: 'BLOB_ANONYMOUS', value: string(blobAnonymous) }
          ], empty(blobSasToken) ? [] : [
            { name: 'BLOB_SAS_TOKEN', secretRef: 'blob-sas-token' }
          ])
          probes: [
            {
              type: 'Startup'
              httpGet: { path: probePath, port: 8000 }
              periodSeconds: 3
              failureThreshold: 20
            }
            {
              type: 'Liveness'
              httpGet: { path: probePath, port: 8000 }
              periodSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: { path: probePath, port: 8000 }
              periodSeconds: 10
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
  dependsOn: [
    acrPull
  ]
}

output registryName string = registry.name
output registryLoginServer string = registry.properties.loginServer
output containerAppName string = deployApp ? app.name : ''
output appUrl string = deployApp ? 'https://${app!.properties.configuration.ingress.fqdn}' : ''
output appInsightsName string = appInsights.name
