# API Gateway Service

API Gateway Service is the entry point for all client requests in the microservices architecture, providing routing, load balancing, and security for the backend services.

## Features

- **Service Proxying**: Route requests to backend services with automatic load balancing
- **Security**: Built-in security features with CORS, Helmet, and rate limiting
- **Monitoring**: Prometheus metrics for performance and health monitoring
- **Logging**: Comprehensive logging for debugging and monitoring
- **Health Checking**: Regular health checks for backend services
- **Service Discovery**: Dynamic service discovery and routing

## Prerequisites

- Node.js 18.x or higher
- npm 9.x or higher

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd microservices/api-gateway
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   # Server Configuration
   PORT=8080
   HOST=0.0.0.0
   NODE_ENV=development

   # Security Configuration
   CORS_ORIGIN=*

   # Rate Limiting Configuration
   RATE_LIMIT_WINDOW_MS=900000
   RATE_LIMIT_MAX=100

   # Logging Configuration
   LOG_LEVEL=info
   LOG_FORMAT=combined
   ```

## Usage

### Start the service

```bash
# Development mode
npm run dev

# Production mode
npm start
```

### API Endpoints

#### Health Check
- **GET** `/health` - Check service health status

#### Service Info
- **GET** `/info` - Get service information

#### Service Status
- **GET** `/status` - Check status of all backend services

#### Monitoring
- **GET** `/metrics` - Prometheus metrics endpoint

### Proxy Routes

The API Gateway automatically routes requests to backend services based on the following patterns:

- **/api/core/** - Routes to Backend Core Service
- **/api/decision/** - Routes to Decision Service
- **/api/edge/** - Routes to Edge Computing Service
- **/api/blockchain/** - Routes to Blockchain Integration Service

## Testing

Run the test suite:

```bash
npm test
```

## CI/CD

This service uses GitHub Actions for CI/CD. The workflow includes:
- Running tests on every push and pull request
- Building the service for production
- Deploying to production environment

## Docker

### Build and run with Docker

```bash
# Build the image
docker build -t api-gateway .

# Run the container
docker run -p 8080:8080 --name api-gateway api-gateway
```

### Run with Docker Compose

See the root `docker-compose.yml` file for running all services together.

## Monitoring

The service exposes Prometheus metrics at `/metrics` endpoint. Key metrics include:

- `http_requests_total` - Total number of HTTP requests
- `http_request_duration_seconds` - HTTP request duration in seconds
- `proxy_requests_total` - Total number of proxy requests
- `proxy_request_duration_seconds` - Proxy request duration in seconds
- `service_health_status` - Service health status (1 = healthy, 0 = unhealthy)
- `target_service_health_status` - Target service health status (1 = healthy, 0 = unhealthy)
- `errors_total` - Total number of errors

## Logging

Logs are written to the console by default. In production, you can configure logging to a file or log management service.

## Security

- **CORS**: Configurable CORS policy
- **Helmet**: Security headers for protection against common web vulnerabilities
- **Rate Limiting**: Protection against brute force attacks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## License

[MIT License](LICENSE)
