import morgan from 'morgan';
import config from '../config/config.js';

// 自定义日志格式
const customFormat = ':date[iso] :method :url :status :response-time ms - :res[content-length] - :req[user-agent]';

// 开发环境日志中间件
const devLogger = morgan('dev');

// 生产环境日志中间件
const prodLogger = morgan(customFormat, {
  skip: (req, res) => res.statusCode < 400,
  stream: {
    write: (message) => {
      // 可以将日志写入文件或日志服务
      console.log(message.trim());
    }
  }
});

// 根据环境选择日志中间件
const loggerMiddleware = process.env.NODE_ENV === 'production' ? prodLogger : devLogger;

// 自定义请求日志函数
const logRequest = (req, message = '') => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url} - ${message}`);
};

// 自定义错误日志函数
const logError = (err, req = null, service = null) => {
  const timestamp = new Date().toISOString();
  const requestInfo = req ? `${req.method} ${req.url}` : 'Unknown Request';
  const serviceInfo = service ? `[${service}]` : '';
  console.error(`[${timestamp}] ERROR ${serviceInfo} - ${requestInfo}`);
  console.error(err);
};

// 自定义信息日志函数
const logInfo = (message, context = '') => {
  console.log(`[${new Date().toISOString()}] INFO - ${context}: ${message}`);
};

// 自定义警告日志函数
const logWarn = (message, context = '') => {
  console.warn(`[${new Date().toISOString()}] WARN - ${context}: ${message}`);
};

// 服务状态日志函数
const logServiceStatus = (serviceName, status, details = {}) => {
  console.log(`[${new Date().toISOString()}] SERVICE - ${serviceName}: ${status}`, details);
};

export {
  loggerMiddleware,
  logRequest,
  logError,
  logInfo,
  logWarn,
  logServiceStatus
};