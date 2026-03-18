import dotenv from 'dotenv';

// 加载环境变量
dotenv.config();

// 配置对象
const config = {
  server: {
    port: process.env.PORT || 8002,
    host: process.env.HOST || '0.0.0.0',
    timeout: process.env.TIMEOUT || 30000,
    environment: process.env.NODE_ENV || 'development'
  },
  api: {
    prefix: process.env.API_PREFIX || '/api/decision'
  },
  security: {
    cors: {
      origin: process.env.CORS_ORIGIN || '*',
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
      credentials: true
    }
  },
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: process.env.LOG_FORMAT || 'combined',
    enabled: process.env.LOG_ENABLED !== 'false'
  },
  health: {
    enabled: process.env.HEALTH_ENABLED !== 'false',
    endpoint: process.env.HEALTH_ENDPOINT || '/health',
    interval: process.env.HEALTH_INTERVAL || 30000
  },
  service: {
    name: 'decision-service',
    version: '1.0.0',
    description: 'Decision service for AI-powered decision making'
  },
  database: {
    uri: process.env.MONGODB_URI || 'mongodb://localhost:27017/decision-service',
    options: {
      useNewUrlParser: true,
      useUnifiedTopology: true
    }
  }
};

export default config;
