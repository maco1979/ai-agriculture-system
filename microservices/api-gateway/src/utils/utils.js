// 生成唯一ID
const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

// 格式化响应数据
const formatResponse = (data, message = 'Success', status = 'success') => {
  return {
    status,
    message,
    data,
    timestamp: new Date().toISOString()
  };
};

// 格式化错误响应
const formatError = (message, status = 'error', code = 500, service = null) => {
  return {
    status,
    message,
    code,
    service,
    timestamp: new Date().toISOString()
  };
};

// 验证请求体
const validateBody = (body, requiredFields = []) => {
  if (!body) {
    return {
      valid: false,
      message: 'Request body is required'
    };
  }
  
  const missingFields = requiredFields.filter(field => !body[field]);
  if (missingFields.length > 0) {
    return {
      valid: false,
      message: `Missing required fields: ${missingFields.join(', ')}`
    };
  }
  
  return {
    valid: true
  };
};

// 验证请求参数
const validateParams = (params, requiredParams = []) => {
  if (!params) {
    return {
      valid: false,
      message: 'Request parameters are required'
    };
  }
  
  const missingParams = requiredParams.filter(param => !params[param]);
  if (missingParams.length > 0) {
    return {
      valid: false,
      message: `Missing required parameters: ${missingParams.join(', ')}`
    };
  }
  
  return {
    valid: true
  };
};

// 检查服务健康状态
const checkServiceHealth = async (serviceUrl, healthEndpoint = '/health') => {
  try {
    const response = await fetch(`${serviceUrl}${healthEndpoint}`);
    return {
      status: response.ok ? 'healthy' : 'unhealthy',
      statusCode: response.status,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    return {
      status: 'unavailable',
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
};

// 延迟函数
const delay = (ms) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// 格式化服务代理配置
const formatProxyConfig = (serviceConfig) => {
  return {
    target: serviceConfig.url,
    changeOrigin: true,
    pathRewrite: {
      [`^${serviceConfig.path}`]: ''
    },
    onError: (err, req, res) => {
      console.error(`Proxy error to ${serviceConfig.name}:`, err);
      res.status(502).json(formatError(
        `Error connecting to ${serviceConfig.name} service`,
        'error',
        502,
        serviceConfig.name
      ));
    },
    onProxyReq: (proxyReq, req, res) => {
      // 可以在这里添加自定义的代理请求头
      proxyReq.setHeader('X-API-Gateway', 'api-gateway');
      proxyReq.setHeader('X-Forwarded-For', req.ip);
    },
    onProxyRes: (proxyRes, req, res) => {
      // 可以在这里处理代理响应
      proxyRes.headers['X-Proxy-By'] = 'api-gateway';
    }
  };
};

export {
  generateId,
  formatResponse,
  formatError,
  validateBody,
  validateParams,
  checkServiceHealth,
  delay,
  formatProxyConfig
};