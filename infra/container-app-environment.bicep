@description('Location for resources')
param location string

@description('Tags for resources')
param tags object

@description('Name of the Container Apps Environment')
param environmentName string

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: 'law-${environmentName}-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
  tags: tags
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
      }
    }
    zoneRedundant: false
  }
  tags: tags
}

output environmentId string = containerAppsEnvironment.id
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id