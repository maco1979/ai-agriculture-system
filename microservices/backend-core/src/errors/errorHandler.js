// 自定义错误类
class AppError extends Error {
  constructor(message, statusCode, isOperational = true, stack = '') {
    super(message);
    this.statusCode = statusCode;
    this.status = `${statusCode}`.startsWith('4') ? 'fail' : 'error';
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
    
    // 处理特定类型的错误
    if (err.name === 'CastError') error = handleCastErrorDB(err);
    if (err.name === 'ValidationError') error = handleValidationErrorDB(err);
    if (err.code === 11000) error = handleDuplicateFieldsDB(err);
    
    sendErrorProd(error, res);
  }
};

// 开发环境错误响应
const sendErrorDev = (err, res) => {
  res.status(err.statusCode).json({
    status: err.status,
    error: err,
    message: err.message,
    stack: err.stack
  });
};

// 生产环境错误响应
const sendErrorProd = (err, res) => {
  // 只发送操作型错误给客户端
  if (err.isOperational) {
    res.status(err.statusCode).json({
      status: err.status,
      message: err.message
    });
  } 
  // 未知错误，记录日志但不暴露给客户端
  else {
    // 记录错误
    console.error('ERROR 💥', err);
    
    // 发送通用错误消息
    res.status(500).json({
      status: 'error',
      message: 'An unexpected error occurred'
    });
  }
};

// 处理数据库类型转换错误
const handleCastErrorDB = (err) => {
  const message = `Invalid ${err.path}: ${err.value}.`;
  return new AppError(message, 400);
};

// 处理数据库验证错误
const handleValidationErrorDB = (err) => {
  const errors = Object.values(err.errors).map(el => el.message);
  const message = `Invalid input data. ${errors.join('. ')}`;
  return new AppError(message, 400);
};

// 处理数据库重复字段错误
const handleDuplicateFieldsDB = (err) => {
  const value = err.errmsg.match(/"([^"]*)"/)[1];
  const message = `Duplicate field value: ${value}. Please use another value.`;
  return new AppError(message, 400);
};

export { AppError, errorHandler };