import { loggerMiddleware, logRequest, logError, logInfo, logWarn } from '../src/middleware/logger';

// 模拟console方法
jest.spyOn(console, 'log').mockImplementation();
jest.spyOn(console, 'error').mockImplementation();
jest.spyOn(console, 'warn').mockImplementation();

describe('Logger Module', () => {
  beforeEach(() => {
    // 清除所有模拟调用
    jest.clearAllMocks();
  });

  describe('loggerMiddleware', () => {
    test('should be defined', () => {
      expect(loggerMiddleware).toBeDefined();
      expect(typeof loggerMiddleware).toBe('function');
    });
  });

  describe('logRequest', () => {
    test('should log request information', () => {
      const req = { method: 'GET', url: '/test' };
      const message = 'Test message';
      
      logRequest(req, message);
      
      expect(console.log).toHaveBeenCalled();
      expect(console.log.mock.calls[0][0]).toMatch(/\[.*\] GET \/test - Test message/);
    });

    test('should log request information without message', () => {
      const req = { method: 'POST', url: '/api/test' };
      
      logRequest(req);
      
      expect(console.log).toHaveBeenCalled();
      expect(console.log.mock.calls[0][0]).toMatch(/\[.*\] POST \/api\/test - /);
    });
  });

  describe('logError', () => {
    test('should log error with request information', () => {
      const err = new Error('Test error');
      const req = { method: 'GET', url: '/test' };
      
      logError(err, req);
      
      expect(console.error).toHaveBeenCalledTimes(2);
      expect(console.error.mock.calls[0][0]).toMatch(/\[.*\] ERROR - GET \/test/);
      expect(console.error.mock.calls[1][0]).toBe(err);
    });

    test('should log error without request information', () => {
      const err = new Error('Test error');
      
      logError(err);
      
      expect(console.error).toHaveBeenCalledTimes(2);
      expect(console.error.mock.calls[0][0]).toMatch(/\[.*\] ERROR - Unknown Request/);
      expect(console.error.mock.calls[1][0]).toBe(err);
    });
  });

  describe('logInfo', () => {
    test('should log information message with context', () => {
      const message = 'Test information';
      const context = 'TestContext';
      
      logInfo(message, context);
      
      expect(console.log).toHaveBeenCalled();
      expect(console.log.mock.calls[0][0]).toMatch(/\[.*\] INFO - TestContext: Test information/);
    });

    test('should log information message without context', () => {
      const message = 'Test information';
      
      logInfo(message);
      
      expect(console.log).toHaveBeenCalled();
      expect(console.log.mock.calls[0][0]).toMatch(/\[.*\] INFO - : Test information/);
    });
  });

  describe('logWarn', () => {
    test('should log warning message with context', () => {
      const message = 'Test warning';
      const context = 'TestContext';
      
      logWarn(message, context);
      
      expect(console.warn).toHaveBeenCalled();
      expect(console.warn.mock.calls[0][0]).toMatch(/\[.*\] WARN - TestContext: Test warning/);
    });

    test('should log warning message without context', () => {
      const message = 'Test warning';
      
      logWarn(message);
      
      expect(console.warn).toHaveBeenCalled();
      expect(console.warn.mock.calls[0][0]).toMatch(/\[.*\] WARN - : Test warning/);
    });
  });
});
