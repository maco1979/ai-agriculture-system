import dotenv from 'dotenv';

// 加载环境变量
dotenv.config();

const config = {
  // 服务器配置
  server: {
    port: process.env.PORT || 8001,
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
  
  // 数据库配置（预留）
  database: {
    host: process.env.DB_HOST,
    port: process.env.DB_PORT,
    name: process.env.DB_NAME,
    username: process.env.DB_USERNAME,
    password: process.env.DB_PASSWORD
  },
  
  // API配置
  api: {
    prefix: '/api',
    version: 'v1',
    rateLimit: {
      enabled: process.env.RATE_LIMIT_ENABLED === 'true',
      windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
      max: parseInt(process.env.RATE_LIMIT_MAX) || 100
    }
  },
  
  // 健康检查配置
  health: {
    enabled: true,
    endpoint: '/health'
  },
  
  // 服务信息
  service: {
    name: 'backend-core',
    version: '1.0.0',
    description: 'Backend Core Service for AI Management'
  }
};

export default config;