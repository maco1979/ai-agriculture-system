import express from 'express';
import config from './config/config.js';
import { errorHandler } from './errors/errorHandler.js';
import { corsMiddleware, helmetMiddleware } from './middleware/security.js';
import { loggerMiddleware } from './middleware/logger.js';
import apiRoutes from './api/routes.js';
import { monitoringMiddleware, metricsHandler } from './utils/monitoring.js';

// 创建Express应用
const app = express();
const PORT = config.server.port;

// 中间件配置
if (config.security.helmet.enabled) {
  app.use(helmetMiddleware);
}
app.use(corsMiddleware);
if (config.logging.enabled) {
  app.use(loggerMiddleware);
}
app.use(express.json({
  limit: '10mb',
  timeout: config.server.timeout
}));
app.use(express.urlencoded({ 
  extended: true,
  limit: '10mb'
}));
// 监控中间件
app.use(monitoringMiddleware);

// 健康检查端点
app.get(config.health.endpoint, (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: config.service.name,
    version: config.service.version,
    environment: config.server.environment
  });
});

// 服务信息端点
app.get('/info', (req, res) => {
  res.status(200).json({
    name: config.service.name,
    version: config.service.version,
    description: config.service.description,
    environment: config.server.environment,
    health: `${req.protocol}://${req.hostname}:${PORT}${config.health.endpoint}`
  });
});

// Prometheus指标端点
app.get('/metrics', metricsHandler);

// 注册API路由
app.use(config.api.prefix, apiRoutes);

// 404处理
app.use((req, res) => {
  res.status(404).json({
    status: 'fail',
    message: 'The requested resource was not found',
    path: req.originalUrl,
    timestamp: new Date().toISOString()
  });
});

// 错误处理中间件
app.use(errorHandler);

// 启动服务器
app.listen(PORT, () => {
  console.log(`🚀 ${config.service.name} running on port ${PORT}`);
  console.log(`📊 Environment: ${config.server.environment}`);
  console.log(`🌡️  Health check: http://localhost:${PORT}${config.health.endpoint}`);
  console.log(`ℹ️  Service info: http://localhost:${PORT}/info`);
  console.log(`📈 Monitoring: http://localhost:${PORT}/metrics`);
});

export default app;
