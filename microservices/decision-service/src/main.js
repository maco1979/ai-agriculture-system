import express from 'express';
import cors from 'cors';
import config from './config/config.js';
import { monitoringMiddleware, metricsHandler, recordDecisionRequest } from './utils/monitoring.js';

// 创建Express应用
const app = express();
const PORT = config.server.port;

// 中间件配置
app.use(cors({
  origin: config.security.cors.origin,
  methods: config.security.cors.methods,
  allowedHeaders: config.security.cors.allowedHeaders,
  credentials: config.security.cors.credentials
}));
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
    service: config.service.name,
    version: config.service.version,
    environment: config.server.environment,
    timestamp: new Date().toISOString()
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

// 决策API端点
app.post('/api/decision/make', async (req, res) => {
  const start = Date.now();
  try {
    const { type, data } = req.body;
    
    // 验证请求
    if (!type || !data) {
      return res.status(400).json({
        status: 'fail',
        message: 'Missing required fields: type and data',
        timestamp: new Date().toISOString()
      });
    }
    
    // 模拟决策过程
    await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 400));
    
    // 生成决策结果
    const decision = {
      type,
      status: 'approved',
      confidence: Math.random() * 0.3 + 0.7, // 70-100%
      timestamp: new Date().toISOString(),
      data: {
        input: data,
        analysis: `Analysis for ${type} decision`,
        recommendation: 'Proceed with action'
      }
    };
    
    const duration = (Date.now() - start) / 1000;
    recordDecisionRequest(type, 'success', duration);
    
    res.status(200).json({
      status: 'success',
      message: 'Decision made successfully',
      data: decision,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    const duration = (Date.now() - start) / 1000;
    recordDecisionRequest('unknown', 'error', duration);
    
    console.error('Error making decision:', error);
    res.status(500).json({
      status: 'error',
      message: 'Failed to make decision',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// 404处理
app.use((req, res) => {
  res.status(404).json({
    status: 'fail',
    message: 'The requested resource was not found',
    path: req.originalUrl,
    timestamp: new Date().toISOString()
  });
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`🚀 ${config.service.name} running on port ${PORT}`);
  console.log(`📊 Environment: ${config.server.environment}`);
  console.log(`🌡️  Health check: http://localhost:${PORT}${config.health.endpoint}`);
  console.log(`ℹ️  Service info: http://localhost:${PORT}/info`);
  console.log(`📈 Monitoring: http://localhost:${PORT}/metrics`);
});

export default app;
