# Backend Core Service

Backend Core Service is the central service for the microservices architecture, providing core functionality for AI model management, inference, and system operations.

## Features

- **AI Model Management**: Upload, manage, and version AI models
- **Inference Engine**: Run inference on AI models with different parameters
- **System Management**: System status, configuration, and health checks
- **Security**: Built-in security features with CORS, Helmet, and rate limiting
- **Monitoring**: Prometheus metrics for performance and health monitoring
- **Logging**: Comprehensive logging for debugging and monitoring

## Prerequisites

- Node.js 18.x or higher
- npm 9.x or higher

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd microservices/backend-core
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   # Server Configuration
   PORT=8001
   HOST=0.0.0.0
   NODE_ENV=development

   # API Configuration
   API_PREFIX=/api/core

   # Security Configuration
   CORS_ORIGIN=*

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

#### AI Model Management
- **GET** `/api/core/models` - List all models
- **POST** `/api/core/models` - Upload a new model
- **GET** `/api/core/models/:id` - Get model details
- **PUT** `/api/core/models/:id` - Update model information
- **DELETE** `/api/core/models/:id` - Delete a model

#### Inference
- **POST** `/api/core/inference` - Run inference on a model
- **POST** `/api/core/inference/batch` - Run batch inference

#### System Management
- **GET** `/api/core/system/status` - Get system status
- **GET** `/api/core/system/config` - Get system configuration
- **PUT** `/api/core/system/config` - Update system configuration

#### AI Control
- **POST** `/api/core/ai/control/train` - Start model training
- **POST** `/api/core/ai/control/stop` - Stop model training
- **GET** `/api/core/ai/control/status` - Get training status

### Monitoring

- **GET** `/metrics` - Prometheus metrics endpoint

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
docker build -t backend-core .

# Run the container
docker run -p 8001:8001 --name backend-core backend-core
```

### Run with Docker Compose

See the root `docker-compose.yml` file for running all services together.

## Monitoring

The service exposes Prometheus metrics at `/metrics` endpoint. Key metrics include:

- `http_requests_total` - Total number of HTTP requests
- `http_request_duration_seconds` - HTTP request duration in seconds
- `service_health_status` - Service health status (1 = healthy, 0 = unhealthy)
- `inference_requests_total` - Total number of inference requests
- `inference_duration_seconds` - Inference execution duration in seconds
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
