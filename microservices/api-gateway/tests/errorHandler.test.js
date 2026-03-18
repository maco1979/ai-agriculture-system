import { GatewayError, errorHandler, createServiceUnavailableError, createProxyError } from '../src/errors/errorHandler.js';

// 模拟 console.error
jest.spyOn(console, 'error').mockImplementation();

describe('Error Handler Module', () => {
  beforeEach(() => {
    // 清除所有模拟调用
    jest.clearAllMocks();
  });

  describe('GatewayError Class', () => {
    test('should create GatewayError with default values', () => {
      const message = 'Test error';
      const statusCode = 404;
      const error = new GatewayError(message, statusCode);

      expect(error).toBeInstanceOf(Error);
      expect(error.message).toBe(message);
      expect(error.statusCode).toBe(statusCode);
      expect(error.status).toBe('fail');
      expect(error.service).toBeNull();
      expect(error.isOperational).toBe(true);
      expect(error.stack).toBeDefined();
    });

    test('should create GatewayError with service name', () => {
      const message = 'Test error';
      const statusCode = 500;
      const service = 'test-service';
      const error = new GatewayError(message, statusCode, service);

      expect(error.service).toBe(service);
      expect(error.status).toBe('error');
    });

    test('should create GatewayError with custom stack', () => {
      const message = 'Test error';
      const statusCode = 400;
      const stack = 'Custom stack trace';
      const error = new GatewayError(message, statusCode, null, true, stack);

      expect(error.stack).toBe(stack);
    });

    test('should set status to error for 500+ status codes', () => {
      const message = 'Server error';
      const statusCode = 500;
      const error = new GatewayError(message, statusCode);

      expect(error.status).toBe('error');
    });

    test('should set status to fail for 400+ status codes', () => {
      const message = 'Bad request';
      const statusCode = 400;
      const error = new GatewayError(message, statusCode);

      expect(error.status).toBe('fail');
    });
  });

  describe('errorHandler Middleware', () => {
    test('should handle error in development environment', () => {
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      const err = new GatewayError('Test error', 404, 'test-service');
      const res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      errorHandler(err, {}, res, () => {});

      expect(res.status).toHaveBeenCalledWith(404);
      expect(res.json).toHaveBeenCalledWith({
        status: 'fail',
        error: err,
        message: 'Test error',
        service: 'test-service',
        stack: err.stack,
        timestamp: expect.any(String)
      });

      // 恢复原始的 NODE_ENV
      process.env.NODE_ENV = originalNodeEnv;
    });

    test('should handle operational error in production environment', () => {
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      const err = new GatewayError('Test error', 404, 'test-service');
      const res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      errorHandler(err, {}, res, () => {});

      expect(res.status).toHaveBeenCalledWith(404);
      expect(res.json).toHaveBeenCalledWith({
        status: 'fail',
        message: 'Test error',
        service: 'test-service',
        timestamp: expect.any(String)
      });

      // 恢复原始的 NODE_ENV
      process.env.NODE_ENV = originalNodeEnv;
    });

    test('should handle non-operational error in production environment', () => {
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      const err = new Error('Test error');
      err.isOperational = false;
      const res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      errorHandler(err, {}, res, () => {});

      expect(console.error).toHaveBeenCalledWith('API Gateway Error 💥', expect.objectContaining({
        isOperational: false,
        message: 'Test error'
      }));
      expect(res.status).toHaveBeenCalledWith(500);
      expect(res.json).toHaveBeenCalledWith({
        status: 'error',
        message: 'An unexpected error occurred in the API Gateway',
        timestamp: expect.any(String)
      });

      // 恢复原始的 NODE_ENV
      process.env.NODE_ENV = originalNodeEnv;
    });

    test('should set default status code and status', () => {
      const err = new Error('Test error');
      const res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      errorHandler(err, {}, res, () => {});

      expect(res.status).toHaveBeenCalledWith(500);
    });
  });

  describe('createServiceUnavailableError', () => {
    test('should create service unavailable error with message', () => {
      const serviceName = 'test-service';
      const message = 'Connection failed';
      const error = createServiceUnavailableError(serviceName, message);

      expect(error).toBeInstanceOf(GatewayError);
      expect(error.message).toBe(`Service ${serviceName} is unavailable: ${message}`);
      expect(error.statusCode).toBe(503);
      expect(error.service).toBe(serviceName);
    });

    test('should create service unavailable error without message', () => {
      const serviceName = 'test-service';
      const error = createServiceUnavailableError(serviceName);

      expect(error.message).toBe(`Service ${serviceName} is unavailable`);
      expect(error.statusCode).toBe(503);
      expect(error.service).toBe(serviceName);
    });
  });

  describe('createProxyError', () => {
    test('should create proxy error with status code', () => {
      const serviceName = 'test-service';
      const originalError = new Error('Connection error');
      originalError.statusCode = 502;
      const error = createProxyError(serviceName, originalError);

      expect(error).toBeInstanceOf(GatewayError);
      expect(error.message).toBe(`Error proxying to ${serviceName}: ${originalError.message}`);
      expect(error.statusCode).toBe(502);
      expect(error.service).toBe(serviceName);
    });

    test('should create proxy error with default status code', () => {
      const serviceName = 'test-service';
      const originalError = new Error('Connection error');
      const error = createProxyError(serviceName, originalError);

      expect(error.statusCode).toBe(502);
    });
  });
});
