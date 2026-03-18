import dotenv from 'dotenv';

// 加载环境变量
dotenv.config();

const config = {
  // 服务器配置
  server: {
    port: process.env.PORT || 8080,
    environment: process.env.NODE_ENV || 'development',
    timeout: parseInt(process.env.SERVER_TIMEOUT) || 30000
  },
  
  // 安全配置
  security: {
    cors: {
      origin: process.env.CORS_ORIGIN || '*',
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
      credentials: process.env.CORS_CREDENTIALS === 'true'
    },
    helmet: {
      enabled: process.env.HELMET_ENABLED !== 'false'
    }
  },
  
  // 日志配置
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: process.env.LOG_FORMAT || 'combined',
    enabled: process.env.LOG_ENABLED !== 'false'
  },
  
  // 速率限制配置
  rateLimit: {
    enabled: process.env.RATE_LIMIT_ENABLED !== 'false',
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
    max: parseInt(process.env.RATE_LIMIT_MAX) || 100,
    standardHeaders: true,
    legacyHeaders: false
  },
  
  // 服务代理配置
  services: {
    backendCore: {
      name: 'backend-core',
      url: process.env.BACKEND_CORE_URL || 'http://localhost:8001',
      path: '/api/core',
      healthEndpoint: '/health'
    },
    decisionService: {
      name: 'decision-service',
      url: process.env.DECISION_SERVICE_URL || 'http://localhost:8002',
      path: '/api/decision',
      healthEndpoint: '/health'
    },
    edgeComputing: {
      name: 'edge-computing',
      url: process.env.EDGE_COMPUTING_URL || 'http://localhost:8003',
      path: '/api/edge',
      healthEndpoint: '/health'
    },
    blockchain: {
      name: 'blockchain-integration',
      url: process.env.BLOCKCHAIN_URL || 'http://localhost:8004',
      path: '/api/blockchain',
      healthEndpoint: '/health'
    },
    monitoringService: {
      name: 'monitoring-service',
      url: process.env.MONITORING_SERVICE_URL || 'http://localhost:8005',
      path: '/api/monitoring',
      healthEndpoint: '/health'
    }
  },
  
  // 健康检查配置
  health: {
    enabled: true,
    endpoint: '/health',
    interval: parseInt(process.env.HEALTH_CHECK_INTERVAL) || 30000
  },
  
  // 服务信息
  service: {
    name: 'api-gateway',
    version: '1.0.0',
    description: 'API Gateway for Microservices'
  }
};

export default config;