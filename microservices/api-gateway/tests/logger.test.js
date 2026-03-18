import { loggerMiddleware, logRequest, logError, logInfo, logWarn, logServiceStatus } from '../src/middleware/logger.js';
import morgan from 'morgan';

// 模拟 console 方法
jest.spyOn(console, 'log').mockImplementation();
jest.spyOn(console, 'error').mockImplementation();
jest.spyOn(console, 'warn').mockImplementation();

// 模拟 morgan
jest.mock('morgan', () => {
  return jest.fn((format, options) => {
    return (req, res, next) => {
      next();
    };
  });
});

describe('Logger Module', () => {
  beforeEach(() => {
    // 清除所有模拟调用
    jest.clearAllMocks();
  });

  test('should export loggerMiddleware', () => {
    expect(loggerMiddleware).toBeDefined();
    expect(typeof loggerMiddleware).toBe('function');
  });

  test('should export all logging functions', () => {
    expect(typeof logRequest).toBe('function');
    expect(typeof logError).toBe('function');
    expect(typeof logInfo).toBe('function');
    expect(typeof logWarn).toBe('function');
    expect(typeof logServiceStatus).toBe('function');
  });

  describe('logRequest', () => {
    test('should log request with message', () => {
      const req = {
        method: 'GET',
        url: '/api/test'
      };
      const message = 'Test message';

      logRequest(req, message);
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining(`GET /api/test - ${message}`)
      );
    });

    test('should log request without message', () => {
      const req = {
        method: 'POST',
        url: '/api/test'
      };

      logRequest(req);
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining(`POST /api/test - `)
      );
    });
  });

  describe('logError', () => {
    test('should log error with request and service', () => {
      const err = new Error('Test error');
      const req = {
        method: 'GET',
        url: '/api/test'
      };
      const service = 'test-service';

      logError(err, req, service);
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining(`ERROR [test-service] - GET /api/test`)
      );
      expect(console.error).toHaveBeenCalledWith(err);
    });

    test('should log error without request', () => {
      const err = new Error('Test error');

      logError(err);
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining(`ERROR  - Unknown Request`)
      );
      expect(console.error).toHaveBeenCalledWith(err);
    });

    test('should log error without service', () => {
      const err = new Error('Test error');
      const req = {
        method: 'GET',
        url: '/api/test'
      };

      logError(err, req);
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining(`ERROR  - GET /api/test`)
      );
      expect(console.error).toHaveBeenCalledWith(err);
    });
  });

  describe('logInfo', () => {
    test('should log info message with context', () => {
      const message = 'Test info';
      const context = 'Test context';

      logInfo(message, context);
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining(`INFO - ${context}: ${message}`)
      );
    });

    test('should log info message without context', () => {
      const message = 'Test info';

      logInfo(message);
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining(`INFO - : ${message}`)
      );
    });
  });

  describe('logWarn', () => {
    test('should log warn message with context', () => {
      const message = 'Test warning';
      const context = 'Test context';

      logWarn(message, context);
      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining(`WARN - ${context}: ${message}`)
      );
    });

    test('should log warn message without context', () => {
      const message = 'Test warning';

      logWarn(message);
      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining(`WARN - : ${message}`)
      );
    });
  });

  describe('logServiceStatus', () => {
    test('should log service status with details', () => {
      const serviceName = 'test-service';
      const status = 'healthy';
      const details = {
        uptime: 1000,
        responseTime: 50
      };

      logServiceStatus(serviceName, status, details);
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining(`SERVICE - ${serviceName}: ${status}`),
        details
      );
    });

    test('should log service status without details', () => {
      const serviceName = 'test-service';
      const status = 'unhealthy';

      logServiceStatus(serviceName, status);
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining(`SERVICE - ${serviceName}: ${status}`),
        {}
      );
    });
  });
});
