# Frontend Web Service

Frontend Web Service is the user-facing interface for the microservices architecture, providing a responsive web application for interacting with the backend services.

## Features

- **Responsive Design**: Mobile-friendly interface that works on all devices
- **Modern UI**: Clean, modern user interface with React and TypeScript
- **Service Integration**: Seamless integration with backend services through the API Gateway
- **Real-time Monitoring**: Dashboard for monitoring service status and performance
- **Decision Making**: Interface for AI-powered decision making
- **Edge Computing**: Interface for edge computing operations
- **Blockchain Integration**: Interface for blockchain operations
- **Frontend Monitoring**: Built-in performance and error monitoring

## Prerequisites

- Node.js 18.x or higher
- npm 9.x or higher

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd microservices/frontend-web
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   # Vite Configuration
   VITE_API_BASE_URL=http://localhost:8080/api
   VITE_APP_TITLE=AI Microservices Platform
   VITE_APP_VERSION=1.0.0
   ```

## Usage

### Start the development server

```bash
npm run dev
```

### Build for production

```bash
npm run build
```

### Preview production build

```bash
npm run preview
```

## Project Structure

```
frontend-web/
├── src/
│   ├── components/        # Reusable React components
│   ├── pages/             # Page components
│   ├── styles/            # CSS styles
│   ├── utils/             # Utility functions
│   ├── App.tsx            # Main App component
│   └── main.tsx           # Entry point
├── public/                # Static assets
├── index.html             # HTML template
├── tsconfig.json          # TypeScript configuration
├── vite.config.ts         # Vite configuration
└── package.json           # Project configuration
```

## Pages

- **Home Page**: Overview of the platform and services
- **Dashboard Page**: Real-time monitoring dashboard
- **Decision Page**: AI-powered decision making interface
- **Edge Computing Page**: Edge computing operations interface
- **Blockchain Page**: Blockchain integration interface
- **Monitoring Page**: Detailed service monitoring interface

## Components

- **Header**: Navigation header with service links
- **Sidebar**: Side navigation for quick access to services
- **Layout**: Main layout component for consistent page structure

## Monitoring

The frontend includes built-in monitoring for:

- **Page Load Performance**: First paint, first contentful paint, and page load time
- **API Call Performance**: Duration and status of API calls
- **Error Tracking**: Unhandled errors and exceptions
- **User Interactions**: Click events and navigation patterns

## CI/CD

This service uses GitHub Actions for CI/CD. The workflow includes:
- Running linting on every push and pull request
- Building the service for production
- Deploying to production environment

## Docker

### Build and run with Docker

```bash
# Build the image
docker build -t frontend-web .

# Run the container
docker run -p 80:80 --name frontend-web frontend-web
```

### Run with Docker Compose

See the root `docker-compose.yml` file for running all services together.

## Security

- **CORS**: Configured to work with the API Gateway
- **Input Validation**: Client-side input validation
- **Error Handling**: Graceful error handling for better user experience

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run linting
   ```bash
   npm run lint
   ```
5. Submit a pull request

## License

[MIT License](LICENSE)
