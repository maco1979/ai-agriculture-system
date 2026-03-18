// 保存原始的 NODE_ENV
const originalNodeEnv = process.env.NODE_ENV;

// 直接设置 NODE_ENV 为 development
process.env.NODE_ENV = 'development';

import { 
  monitoringMiddleware, 
  metricsHandler, 
  recordDecisionRequest, 
  recordError 
} from '../src/utils/monitoring.js';

// 在测试结束后恢复原始的 NODE_ENV
afterAll(() => {
  process.env.NODE_ENV = originalNodeEnv;
});

describe('Monitoring Module', () => {
  test('should export monitoringMiddleware', () => {
    expect(monitoringMiddleware).toBeDefined();
    expect(typeof monitoringMiddleware).toBe('function');
  });

  test('should export metricsHandler', () => {
    expect(metricsHandler).toBeDefined();
    expect(typeof metricsHandler).toBe('function');
  });

  test('should export recordDecisionRequest', () => {
    expect(recordDecisionRequest).toBeDefined();
    expect(typeof recordDecisionRequest).toBe('function');
  });

  test('should export recordError', () => {
    expect(recordError).toBeDefined();
    expect(typeof recordError).toBe('function');
  });

  test('should call recordDecisionRequest without error', () => {
    expect(() => {
      recordDecisionRequest('approval', 'success', 0.5);
    }).not.toThrow();
  });

  test('should call recordError without error', () => {
    expect(() => {
      recordError('database');
    }).not.toThrow();
  });

  test('should call monitoringMiddleware without error', () => {
    const req = {
      method: 'GET',
      url: '/test'
    };
    const res = {
      on: jest.fn((event, callback) => {
        if (event === 'finish') {
          callback();
        }
      })
    };
    const next = jest.fn();

    expect(() => {
      monitoringMiddleware(req, res, next);
    }).not.toThrow();
    expect(next).toHaveBeenCalled();
  });

  test('should call metricsHandler without error', () => {
    const req = {};
    const res = {
      set: jest.fn(),
      end: jest.fn()
    };

    expect(() => {
      metricsHandler(req, res);
    }).not.toThrow();
  });
});
