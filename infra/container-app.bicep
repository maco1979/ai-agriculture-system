@description('Location for resources')
param location string

@description('Tags for resources')
param tags object

@description('Name of the Container App')
param appName string

@description('Container Apps Environment ID')
param environmentId string

@description('Container registry server')
param registryServer string

@description('Container image name')
param imageName string

@description('Container port')
param port int

@description('CPU allocation')
param cpu float

@description('Memory allocation')
param memory string

@description('Minimum replicas')
param minReplicas int

@description('Maximum replicas')
param maxReplicas int

resource containerApp 'Microsoft.App/containerApps@2022-03-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      ingress: {
        external: true
        targetPort: port
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      registries: [
        {
          server: registryServer
          username: '${ContainerRegistryUsername}' // Will be provided during deployment
          passwordSecretRef: 'registry-password'
        }
      ]
      secrets: [
        {
          name: 'registry-password'
          value: '${ContainerRegistryPassword}' // Will be provided during deployment
        }
      ]
    }
    template: {
      containers: [
        {
          name: appName
          image: '${registryServer}/${imageName}'
          resources: {
            cpu: cpu
            memory: memory
          }
          env: [
            {
              name: 'PORT'
              value: '${port}'
            }
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
  tags: tags
}

output hostname string = containerApp.properties.configuration.ingress.fqdn
output appId string = containerApp.id