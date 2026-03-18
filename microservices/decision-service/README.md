# Decision Service

Decision Service is an AI-powered decision making service for the microservices architecture, providing intelligent decision making capabilities for various use cases.

## Features

- **AI-powered Decision Making**: Intelligent decision making based on input data
- **Multi-type Decisions**: Support for different types of decisions (approval, routing, prioritization, etc.)
- **Confidence Scoring**: Provides confidence scores for decisions
- **Security**: Built-in security features with CORS
- **Monitoring**: Prometheus metrics for performance and health monitoring
- **Logging**: Comprehensive logging for debugging and monitoring

## Prerequisites

- Node.js 18.x or higher
- npm 9.x or higher

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd microservices/decision-service
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   # Server Configuration
   PORT=8002
   HOST=0.0.0.0
   NODE_ENV=development

   # API Configuration
   API_PREFIX=/api/decision

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

#### Decision Making
- **POST** `/api/decision/make` - Make a decision based on input data

### Request Body for Decision Making

```json
{
  "type": "approval",
  "data": {
    "user_id": "123",
    "amount": 1000,
    "risk_score": 0.75,
    "history": [
      { "action": "approve", "amount": 500, "timestamp": "2023-01-01T00:00:00Z" },
      { "action": "approve", "amount": 750, "timestamp": "2023-02-01T00:00:00Z" }
    ]
  }
}
```

### Response for Decision Making

```json
{
  "status": "success",
  "message": "Decision made successfully",
  "data": {
    "type": "approval",
    "status": "approved",
    "confidence": 0.85,
    "timestamp": "2023-03-01T00:00:00Z",
    "data": {
      "input": {
        "user_id": "123",
        "amount": 1000,
        "risk_score": 0.75,
        "history": [
          { "action": "approve", "amount": 500, "timestamp": "2023-01-01T00:00:00Z" },
          { "action": "approve", "amount": 750, "timestamp": "2023-02-01T00:00:00Z" }
        ]
      },
      "analysis": "Analysis for approval decision",
      "recommendation": "Proceed with action"
    }
  },
  "timestamp": "2023-03-01T00:00:00Z"
}
```

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
docker build -t decision-service .

# Run the container
docker run -p 8002:8002 --name decision-service decision-service
```

### Run with Docker Compose

See the root `docker-compose.yml` file for running all services together.

## Monitoring

The service exposes Prometheus metrics at `/metrics` endpoint. Key metrics include:

- `http_requests_total` - Total number of HTTP requests
- `http_request_duration_seconds` - HTTP request duration in seconds
- `service_health_status` - Service health status (1 = healthy, 0 = unhealthy)
- `decision_requests_total` - Total number of decision requests
- `decision_duration_seconds` - Decision execution duration in seconds
- `errors_total` - Total number of errors

## Logging

Logs are written to the console by default. In production, you can configure logging to a file or log management service.

## Security

- **CORS**: Configurable CORS policy

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## License

[MIT License](LICENSE)
