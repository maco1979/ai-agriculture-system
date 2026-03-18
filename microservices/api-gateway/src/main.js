import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import config from './config/config.js';
import { errorHandler } from './errors/errorHandler.js';
import { corsMiddleware, helmetMiddleware, rateLimitMiddleware } from './middleware/security.js';
import { loggerMiddleware, logInfo, logServiceStatus } from './middleware/logger.js';
import { getProxyConfigs } from './proxy/proxyConfig.js';
import { formatResponse, checkServiceHealth } from './utils/utils.js';
import { monitoringMiddleware, metricsHandler, updateTargetServiceHealthStatus } from './utils/monitoring.js';

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
if (config.rateLimit.enabled) {
  app.use(rateLimitMiddleware);
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
  res.status(200).json(formatResponse({
    status: 'healthy',
    service: config.service.name,
    version: config.service.version,
    environment: config.server.environment
  }, 'API Gateway health check successful'));
});

// 服务信息端点
app.get('/info', (req, res) => {
  res.status(200).json(formatResponse({
    name: config.service.name,
    version: config.service.version,
    description: config.service.description,
    environment: config.server.environment,
    health: `${req.protocol}://${req.hostname}:${PORT}${config.health.endpoint}`,
    services: Object.entries(config.services).map(([key, service]) => ({
      name: service.name,
      path: service.path,
      url: service.url
    }))
  }, 'API Gateway information retrieved successfully'));
});

// Prometheus指标端点
app.get('/metrics', metricsHandler);

// 服务状态检查端点
app.get('/status', async (req, res) => {
  try {
    // 并行检查所有服务的健康状态
    const serviceStatusPromises = Object.entries(config.services).map(async ([key, service]) => {
      const status = await checkServiceHealth(service.url, service.healthEndpoint);
      logServiceStatus(service.name, status.status);
      // 更新目标服务健康状态指标
      updateTargetServiceHealthStatus(service.name, status.status);
      return {
        [service.name]: status
      };
    });

    const serviceStatuses = await Promise.all(serviceStatusPromises);
    const statusMap = serviceStatuses.reduce((acc, status) => {
      return { ...acc, ...status };
    }, {});

    res.status(200).json(formatResponse({
      status: 'online',
      services: statusMap
    }, 'Service status check completed successfully'));
  } catch (error) {
    res.status(500).json(formatResponse({
      status: 'error',
      error: error.message
    }, 'Service status check failed', 'error'));
  }
});

// 注册代理中间件
const proxyConfigs = getProxyConfigs();
Object.entries(proxyConfigs).forEach(([serviceName, proxyConfig]) => {
  app.use(proxyConfig.path, createProxyMiddleware(proxyConfig.config));
  logInfo(`Registered proxy route: ${proxyConfig.path} -> ${proxyConfig.config.target}`, 'Proxy');
});

// 404处理
app.use((req, res) => {
  res.status(404).json(formatResponse({
    error: 'Not Found',
    path: req.originalUrl
  }, 'The requested resource was not found', 'error'));
});

// 错误处理中间件
app.use(errorHandler);

// 启动服务器
app.listen(PORT, () => {
  logInfo(`🚀 ${config.service.name} running on port ${PORT}`, 'Server');
  logInfo(`📊 Environment: ${config.server.environment}`, 'Server');
  logInfo(`🌡️  Health check: http://localhost:${PORT}${config.health.endpoint}`, 'Server');
  logInfo(`ℹ️  Service info: http://localhost:${PORT}/info`, 'Server');
  logInfo(`📋 Service status: http://localhost:${PORT}/status`, 'Server');
  logInfo(`📈 Monitoring: http://localhost:${PORT}/metrics`, 'Server');
  logInfo('🔗 Proxy routes registered:', 'Proxy');
  Object.entries(proxyConfigs).forEach(([serviceName, proxyConfig]) => {
    logInfo(`  ${serviceName}: ${proxyConfig.path} -> ${proxyConfig.config.target}`, 'Proxy');
  });
});

export default app;
