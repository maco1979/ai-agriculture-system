// 自定义错误类
class GatewayError extends Error {
  constructor(message, statusCode, service = null, isOperational = true, stack = '') {
    super(message);
    this.statusCode = statusCode;
    this.status = `${statusCode}`.startsWith('4') ? 'fail' : 'error';
    this.service = service;
    this.isOperational = isOperational;
    
    if (stack) {
      this.stack = stack;
    } else {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

// 错误处理中间件
const errorHandler = (err, req, res, next) => {
  // 设置默认值
  err.statusCode = err.statusCode || 500;
  err.status = err.status || 'error';
  
  // 开发环境显示详细错误信息
  if (process.env.NODE_ENV === 'development') {
    sendErrorDev(err, res);
  } 
  // 生产环境隐藏敏感错误信息
  else {
    let error = { ...err };
    error.message = err.message;
    
    sendErrorProd(error, res);
  }
};

// 开发环境错误响应
const sendErrorDev = (err, res) => {
  res.status(err.statusCode).json({
    status: err.status,
    error: err,
    message: err.message,
    service: err.service,
    stack: err.stack,
    timestamp: new Date().toISOString()
  });
};

// 生产环境错误响应
const sendErrorProd = (err, res) => {
  // 只发送操作型错误给客户端
  if (err.isOperational) {
    res.status(err.statusCode).json({
      status: err.status,
      message: err.message,
      service: err.service,
      timestamp: new Date().toISOString()
    });
  } 
  // 未知错误，记录日志但不暴露给客户端
  else {
    // 记录错误
    console.error('API Gateway Error 💥', err);
    
    // 发送通用错误消息
    res.status(500).json({
      status: 'error',
      message: 'An unexpected error occurred in the API Gateway',
      timestamp: new Date().toISOString()
    });
  }
};

// 服务不可用错误
const createServiceUnavailableError = (serviceName, message = '') => {
  return new GatewayError(
    `Service ${serviceName} is unavailable${message ? ': ' + message : ''}`,
    503,
    serviceName
  );
};

// 代理错误
const createProxyError = (serviceName, error) => {
  return new GatewayError(
    `Error proxying to ${serviceName}: ${error.message}`,
    error.statusCode || 502,
    serviceName
  );
};

export {
  GatewayError,
  errorHandler,
  createServiceUnavailableError,
  createProxyError
};