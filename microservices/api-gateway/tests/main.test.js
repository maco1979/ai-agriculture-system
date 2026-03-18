// 保存原始的 NODE_ENV
const originalNodeEnv = process.env.NODE_ENV;

// 直接设置 NODE_ENV 为 development
process.env.NODE_ENV = 'development';

import request from 'supertest';
import app from '../src/main.js';
import { checkServiceHealth, formatResponse } from '../src/utils/utils.js';
import { getProxyConfigs } from '../src/proxy/proxyConfig.js';
import { logInfo, logServiceStatus } from '../src/middleware/logger.js';

// 在测试结束后恢复原始的 NODE_ENV
afterAll(() => {
  process.env.NODE_ENV = originalNodeEnv;
});

// 模拟依赖
jest.mock('../src/utils/utils.js', () => {
  return {
    checkServiceHealth: jest.fn(),
    formatResponse: jest.fn((data, message = 'Success', status = 'success') => {
      return {
        status,
        message,
        data,
        timestamp: new Date().toISOString()
      };
    })
  };
});

jest.mock('../src/proxy/proxyConfig.js', () => {
  return {
    getProxyConfigs: jest.fn(() => {
      return {
        backendCore: {
          path: '/api/core',
          config: {
            target: 'http://localhost:8001',
            changeOrigin: true,
            pathRewrite: {
              '^/api/core': ''
            }
          }
        }
      };
    })
  };
});

jest.mock('../src/middleware/logger.js', () => {
  return {
    logInfo: jest.fn(),
    logServiceStatus: jest.fn(),
    loggerMiddleware: (req, res, next) => next()
  };
});

// 模拟 http-proxy-middleware
jest.mock('http-proxy-middleware', () => {
  return {
    createProxyMiddleware: jest.fn(() => {
      return (req, res, next) => {
        next();
      };
    })
  };
});

describe('API Gateway Main Module', () => {
  beforeEach(() => {
    // 清除所有模拟调用
    jest.clearAllMocks();
  });

  describe('Health Check Endpoint', () => {
    test('should return 200 for health check', async () => {
      const response = await request(app).get('/health');
      expect(response.status).toBe(200);
      expect(response.body.status).toBe('success');
      expect(formatResponse).toHaveBeenCalled();
    });
  });

  describe('Service Info Endpoint', () => {
    test('should return 200 for service info', async () => {
      const response = await request(app).get('/info');
      expect(response.status).toBe(200);
      expect(response.body.status).toBe('success');
      expect(formatResponse).toHaveBeenCalled();
    });
  });

  describe('Service Status Endpoint', () => {
    test('should return 200 for service status with healthy services', async () => {
      // 模拟服务健康状态
      checkServiceHealth.mockResolvedValue({
        status: 'healthy',
        statusCode: 200,
        timestamp: new Date().toISOString()
      });

      const response = await request(app).get('/status');
      expect(response.status).toBe(200);
      expect(response.body.status).toBe('success');
      expect(checkServiceHealth).toHaveBeenCalled();
      expect(logServiceStatus).toHaveBeenCalled();
    });

    test('should return 500 for service status when check fails', async () => {
      // 模拟服务健康检查失败
      checkServiceHealth.mockRejectedValue(new Error('Service check failed'));

      const response = await request(app).get('/status');
      expect(response.status).toBe(500);
      expect(response.body.status).toBe('error');
    });
  });

  describe('404 Handling', () => {
    test('should return 404 for non-existent routes', async () => {
      const response = await request(app).get('/non-existent-route');
      expect(response.status).toBe(404);
      expect(response.body.status).toBe('error');
      expect(formatResponse).toHaveBeenCalled();
    });
  });

  test('should export app instance', () => {
    expect(app).toBeDefined();
    expect(typeof app.listen).toBe('function');
  });
});
