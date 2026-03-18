targetScope = 'subscription'

@description('Location for all resources.')
param location string = 'eastasia'

@description('Name of the resource group')
param resourceGroupName string = 'rg-ai-agriculture-${uniqueString(subscription().id)}'

@description('Tags for resources')
param tags object = {
  environment: 'production'
  project: 'ai-agriculture'
  costCenter: 'free-tier'
}

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module containerAppEnv './container-app-environment.bicep' = {
  name: 'containerAppEnv'
  scope: rg
  params: {
    location: location
    tags: tags
    environmentName: 'cae-ai-agriculture'
  }
}

module staticWebApp './static-web-app.bicep' = {
  name: 'staticWebApp'
  scope: rg
  params: {
    location: location
    tags: tags
    appName: 'swa-ai-agriculture-${uniqueString(rg.id)}'
    repositoryUrl: 'https://github.com/placeholder/ai-agriculture'
    branch: 'main'
    appLocation: '/frontend'
    outputLocation: 'dist'
    apiLocation: ''
  }
}

module containerApp './container-app.bicep' = {
  name: 'containerApp'
  scope: rg
  params: {
    location: location
    tags: tags
    appName: 'ca-ai-agriculture-backend-${uniqueString(rg.id)}'
    environmentId: containerAppEnv.outputs.environmentId
    registryServer: 'ghcr.io'
    imageName: 'ai-agriculture-backend:latest'
    port: 8000
    cpu: 0.25
    memory: '0.5Gi'
    minReplicas: 0
    maxReplicas: 1
  }
}

module storage './storage.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    location: location
    tags: tags
    storageAccountName: 'staiagri${uniqueString(rg.id)}'
  }
}

module insights './insights.bicep' = {
  name: 'insights'
  scope: rg
  params: {
    location: location
    tags: tags
    appName: 'appi-ai-agriculture-${uniqueString(rg.id)}'
  }
}

output frontendUrl string = staticWebApp.outputs.hostname
output backendUrl string = containerApp.outputs.hostname
output storageAccountName string = storage.outputs.storageAccountName
output insightsConnectionString string = insights.outputs.connectionString