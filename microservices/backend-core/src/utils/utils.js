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
const formatError = (message, status = 'error', code = 500) => {
  return {
    status,
    message,
    code,
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

// 延迟函数
const delay = (ms) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// 检查是否为有效的JSON
const isValidJson = (str) => {
  try {
    JSON.parse(str);
    return true;
  } catch (e) {
    return false;
  }
};

// 安全地解析JSON
const safeParseJson = (str, defaultValue = {}) => {
  try {
    return JSON.parse(str);
  } catch (e) {
    return defaultValue;
  }
};

// 生成随机字符串
const generateRandomString = (length = 10) => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
};

// 格式化时间戳
const formatTimestamp = (timestamp) => {
  return new Date(timestamp).toISOString();
};

// 计算执行时间
const measureExecutionTime = (fn) => {
  const start = Date.now();
  const result = fn();
  const end = Date.now();
  return {
    result,
    executionTime: end - start
  };
};

export {
  generateId,
  formatResponse,
  formatError,
  validateBody,
  validateParams,
  delay,
  isValidJson,
  safeParseJson,
  generateRandomString,
  formatTimestamp,
  measureExecutionTime
};