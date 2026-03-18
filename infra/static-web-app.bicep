@description('Location for resources')
param location string

@description('Tags for resources')
param tags object

@description('Name of the Static Web App')
param appName string

@description('GitHub repository URL')
param repositoryUrl string

@description('GitHub branch name')
param branch string

@description('Location of the application within the repository')
param appLocation string

@description('Output location of the built application')
param outputLocation string

@description('API location (if any)')
param apiLocation string

resource staticWebApp 'Microsoft.Web/staticSites@2022-03-01' = {
  name: appName
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    repositoryUrl: repositoryUrl
    branch: branch
    repositoryToken: '${GitHubToken}' // Will be provided during deployment
    buildProperties: {
      appLocation: appLocation
      apiLocation: apiLocation
      outputLocation: outputLocation
    }
  }
  tags: tags
}

output hostname string = staticWebApp.properties.defaultHostname
output apiKey string = listSecrets(staticWebApp.id, staticWebApp.apiVersion).properties.apiKey