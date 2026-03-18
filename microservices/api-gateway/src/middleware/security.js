import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import config from '../config/config.js';

// CORS中间件
const corsMiddleware = cors({
  origin: config.security.cors.origin,
  methods: config.security.cors.methods,
  allowedHeaders: config.security.cors.allowedHeaders,
  credentials: config.security.cors.credentials,
  optionsSuccessStatus: 200
});

// Helmet安全中间件
const helmetMiddleware = helmet({
  crossOriginResourcePolicy: { policy: "cross-origin" },
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https:"],
      fontSrc: ["'self'", "data:"],
      objectSrc: ["'none'"],
      upgradeInsecureRequests: []
    }
  }
});

// 速率限制中间件
const rateLimitMiddleware = rateLimit({
  windowMs: config.rateLimit.windowMs,
  max: config.rateLimit.max,
  standardHeaders: config.rateLimit.standardHeaders,
  legacyHeaders: config.rateLimit.legacyHeaders,
  message: {
    status: 'error',
    message: 'Too many requests from this IP, please try again later.',
    timestamp: new Date().toISOString()
  }
});

// 身份验证中间件（预留）
const authMiddleware = (req, res, next) => {
  // 实现身份验证逻辑
  next();
};

// 权限检查中间件（预留）
const permissionMiddleware = (requiredPermission) => {
  return (req, res, next) => {
    // 实现权限检查逻辑
    next();
  };
};

export {
  corsMiddleware,
  helmetMiddleware,
  rateLimitMiddleware,
  authMiddleware,
  permissionMiddleware
};