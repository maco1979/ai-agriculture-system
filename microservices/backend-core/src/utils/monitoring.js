import client from 'prom-client';

// 初始化注册表
const register = new client.Registry();

// 配置默认标签
register.setDefaultLabels({
  app: 'backend-core',
  service: 'backend-core'
});

// 收集所有默认指标
client.collectDefaultMetrics({
  register,
  timeout: 10000,
  gcDurationBuckets: [0.001, 0.01, 0.1, 1, 2, 5]
});

// 请求计数器
const httpRequestCounter = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status']
});

// 请求响应时间直方图
const httpRequestDurationHistogram = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration in seconds',
  labelNames: ['method', 'route', 'status'],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
});

// 服务健康状态指标
const serviceHealthGauge = new client.Gauge({
  name: 'service_health_status',
  help: 'Service health status (1 = healthy, 0 = unhealthy)',
  labelNames: ['service']
});

// 模型加载状态指标
const modelLoadGauge = new client.Gauge({
  name: 'model_load_status',
  help: 'Model load status (1 = loaded, 0 = not loaded)',
  labelNames: ['model_name']
});

// 推理请求计数器
const inferenceRequestCounter = new client.Counter({
  name: 'inference_requests_total',
  help: 'Total number of inference requests',
  labelNames: ['model', 'status']
});

// 推理执行时间直方图
const inferenceDurationHistogram = new client.Histogram({
  name: 'inference_duration_seconds',
  help: 'Inference execution duration in seconds',
  labelNames: ['model'],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
});

// 错误计数器
const errorCounter = new client.Counter({
  name: 'errors_total',
  help: 'Total number of errors',
  labelNames: ['type', 'service']
});

// 注册所有指标
register.registerMetric(httpRequestCounter);
register.registerMetric(httpRequestDurationHistogram);
register.registerMetric(serviceHealthGauge);
register.registerMetric(modelLoadGauge);
register.registerMetric(inferenceRequestCounter);
register.registerMetric(inferenceDurationHistogram);
register.registerMetric(errorCounter);

// 监控中间件
const monitoringMiddleware = (req, res, next) => {
  const start = Date.now();
  const route = req.route ? req.route.path : req.path;

  // 监听响应结束事件
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    const status = res.statusCode;

    // 增加请求计数
    httpRequestCounter.inc({ method: req.method, route, status });

    // 记录响应时间
    httpRequestDurationHistogram.observe({ method: req.method, route, status }, duration);
  });

  next();
};

// 暴露指标的端点处理函数
const metricsHandler = async (req, res) => {
  try {
    // 设置服务健康状态为1（健康）
    serviceHealthGauge.set({ service: 'backend-core' }, 1);

    // 返回指标
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
  } catch (error) {
    console.error('Error exposing metrics:', error);
    res.status(500).json({
      status: 'error',
      message: 'Failed to expose metrics'
    });
  }
};

// 记录推理请求
const recordInferenceRequest = (model, status, duration) => {
  inferenceRequestCounter.inc({ model, status });
  if (duration) {
    inferenceDurationHistogram.observe({ model }, duration);
  }
};

// 记录错误
const recordError = (type, service = 'backend-core') => {
  errorCounter.inc({ type, service });
};

// 更新模型加载状态
const updateModelLoadStatus = (modelName, status) => {
  modelLoadGauge.set({ model_name: modelName }, status ? 1 : 0);
};

export {
  register,
  monitoringMiddleware,
  metricsHandler,
  recordInferenceRequest,
  recordError,
  updateModelLoadStatus,
  httpRequestCounter,
  httpRequestDurationHistogram,
  serviceHealthGauge,
  modelLoadGauge,
  inferenceRequestCounter,
  inferenceDurationHistogram,
  errorCounter
};
