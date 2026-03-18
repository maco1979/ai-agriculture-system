import {
  generateId,
  formatResponse,
  formatError,
  validateBody,
  validateParams,
  checkServiceHealth,
  delay,
  formatProxyConfig
} from '../src/utils/utils.js';

// 模拟 fetch 函数
global.fetch = jest.fn();

// 模拟 console.error
jest.spyOn(console, 'error').mockImplementation();

describe('Utils Module', () => {
  beforeEach(() => {
    // 清除所有模拟调用
    jest.clearAllMocks();
  });

  describe('generateId', () => {
    test('should generate a non-empty string', () => {
      const id = generateId();
      expect(typeof id).toBe('string');
      expect(id.length).toBeGreaterThan(0);
    });

    test('should generate unique IDs', () => {
      const id1 = generateId();
      const id2 = generateId();
      expect(id1).not.toBe(id2);
    });
  });

  describe('formatResponse', () => {
    test('should format response with default values', () => {
      const data = { key: 'value' };
      const response = formatResponse(data);
      
      expect(response).toEqual({
        status: 'success',
        message: 'Success',
        data,
        timestamp: expect.any(String)
      });
    });

    test('should format response with custom message', () => {
      const data = { key: 'value' };
      const message = 'Custom message';
      const response = formatResponse(data, message);
      
      expect(response.message).toBe(message);
    });

    test('should format response with custom status', () => {
      const data = { key: 'value' };
      const status = 'custom';
      const response = formatResponse(data, 'Message', status);
      
      expect(response.status).toBe(status);
    });
  });

  describe('formatError', () => {
    test('should format error with default values', () => {
      const message = 'Test error';
      const error = formatError(message);
      
      expect(error).toEqual({
        status: 'error',
        message,
        code: 500,
        service: null,
        timestamp: expect.any(String)
      });
    });

    test('should format error with custom status', () => {
      const message = 'Test error';
      const status = 'fail';
      const error = formatError(message, status);
      
      expect(error.status).toBe(status);
    });

    test('should format error with custom code', () => {
      const message = 'Test error';
      const code = 400;
      const error = formatError(message, 'error', code);
      
      expect(error.code).toBe(code);
    });

    test('should format error with service name', () => {
      const message = 'Test error';
      const service = 'test-service';
      const error = formatError(message, 'error', 500, service);
      
      expect(error.service).toBe(service);
    });
  });

  describe('validateBody', () => {
    test('should return invalid for empty body', () => {
      const result = validateBody(null, ['field1']);
      expect(result.valid).toBe(false);
      expect(result.message).toBe('Request body is required');
    });

    test('should return valid for body with all required fields', () => {
      const body = { field1: 'value1', field2: 'value2' };
      const requiredFields = ['field1', 'field2'];
      const result = validateBody(body, requiredFields);
      expect(result.valid).toBe(true);
    });

    test('should return invalid for body missing required fields', () => {
      const body = { field1: 'value1' };
      const requiredFields = ['field1', 'field2'];
      const result = validateBody(body, requiredFields);
      expect(result.valid).toBe(false);
      expect(result.message).toBe('Missing required fields: field2');
    });

    test('should return valid for empty required fields array', () => {
      const body = { field1: 'value1' };
      const result = validateBody(body, []);
      expect(result.valid).toBe(true);
    });
  });

  describe('validateParams', () => {
    test('should return invalid for empty params', () => {
      const result = validateParams(null, ['param1']);
      expect(result.valid).toBe(false);
      expect(result.message).toBe('Request parameters are required');
    });

    test('should return valid for params with all required parameters', () => {
      const params = { param1: 'value1', param2: 'value2' };
      const requiredParams = ['param1', 'param2'];
      const result = validateParams(params, requiredParams);
      expect(result.valid).toBe(true);
    });

    test('should return invalid for params missing required parameters', () => {
      const params = { param1: 'value1' };
      const requiredParams = ['param1', 'param2'];
      const result = validateParams(params, requiredParams);
      expect(result.valid).toBe(false);
      expect(result.message).toBe('Missing required parameters: param2');
    });

    test('should return valid for empty required parameters array', () => {
      const params = { param1: 'value1' };
      const result = validateParams(params, []);
      expect(result.valid).toBe(true);
    });
  });

  describe('checkServiceHealth', () => {
    test('should return healthy status for successful response', async () => {
      const mockResponse = {
        ok: true,
        status: 200
      };
      global.fetch.mockResolvedValue(mockResponse);

      const result = await checkServiceHealth('http://localhost:8001');
      expect(result.status).toBe('healthy');
      expect(result.statusCode).toBe(200);
      expect(result.timestamp).toBeDefined();
    });

    test('should return unhealthy status for unsuccessful response', async () => {
      const mockResponse = {
        ok: false,
        status: 500
      };
      global.fetch.mockResolvedValue(mockResponse);

      const result = await checkServiceHealth('http://localhost:8001');
      expect(result.status).toBe('unhealthy');
      expect(result.statusCode).toBe(500);
      expect(result.timestamp).toBeDefined();
    });

    test('should return unavailable status for fetch error', async () => {
      const mockError = new Error('Network error');
      global.fetch.mockRejectedValue(mockError);

      const result = await checkServiceHealth('http://localhost:8001');
      expect(result.status).toBe('unavailable');
      expect(result.error).toBe('Network error');
      expect(result.timestamp).toBeDefined();
    });
  });

  describe('delay', () => {
    test('should resolve after specified time', async () => {
      const delayTime = 100;
      const start = Date.now();
      await delay(delayTime);
      const end = Date.now();
      expect(end - start).toBeGreaterThanOrEqual(delayTime);
    });
  });

  describe('formatProxyConfig', () => {
    test('should format proxy config correctly', () => {
      const serviceConfig = {
        name: 'test-service',
        url: 'http://localhost:8000',
        path: '/api/test'
      };

      const config = formatProxyConfig(serviceConfig);
      expect(config.target).toBe(serviceConfig.url);
      expect(config.changeOrigin).toBe(true);
      expect(config.pathRewrite[`^${serviceConfig.path}`]).toBe('');
      expect(typeof config.onError).toBe('function');
      expect(typeof config.onProxyReq).toBe('function');
      expect(typeof config.onProxyRes).toBe('function');
    });

    test('should handle proxy error correctly', () => {
      const serviceConfig = {
        name: 'test-service',
        url: 'http://localhost:8000',
        path: '/api/test'
      };

      const config = formatProxyConfig(serviceConfig);
      const err = new Error('Proxy error');
      const req = {};
      const res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      config.onError(err, req, res);
      expect(console.error).toHaveBeenCalledWith(`Proxy error to ${serviceConfig.name}:`, err);
      expect(res.status).toHaveBeenCalledWith(502);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        status: 'error',
        message: `Error connecting to ${serviceConfig.name} service`,
        code: 502,
        service: serviceConfig.name
      }));
    });

    test('should set headers in onProxyReq', () => {
      const serviceConfig = {
        name: 'test-service',
        url: 'http://localhost:8000',
        path: '/api/test'
      };

      const config = formatProxyConfig(serviceConfig);
      const proxyReq = {
        setHeader: jest.fn()
      };
      const req = {
        ip: '127.0.0.1'
      };
      const res = {};

      config.onProxyReq(proxyReq, req, res);
      expect(proxyReq.setHeader).toHaveBeenCalledWith('X-API-Gateway', 'api-gateway');
      expect(proxyReq.setHeader).toHaveBeenCalledWith('X-Forwarded-For', req.ip);
    });

    test('should set headers in onProxyRes', () => {
      const serviceConfig = {
        name: 'test-service',
        url: 'http://localhost:8000',
        path: '/api/test'
      };

      const config = formatProxyConfig(serviceConfig);
      const proxyRes = {
        headers: {}
      };
      const req = {};
      const res = {};

      config.onProxyRes(proxyRes, req, res);
      expect(proxyRes.headers['X-Proxy-By']).toBe('api-gateway');
    });
  });
});
