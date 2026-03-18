// 保存原始的 NODE_ENV
const originalNodeEnv = process.env.NODE_ENV;

// 直接设置 NODE_ENV 为 development
process.env.NODE_ENV = 'development';

import { corsMiddleware, helmetMiddleware, rateLimitMiddleware, authMiddleware, permissionMiddleware } from '../src/middleware/security.js';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';

// 在测试结束后恢复原始的 NODE_ENV
afterAll(() => {
  process.env.NODE_ENV = originalNodeEnv;
});

// 模拟 cors
jest.mock('cors', () => {
  return jest.fn(() => {
    return (req, res, next) => {
      next();
    };
  });
});

// 模拟 helmet
jest.mock('helmet', () => {
  return jest.fn(() => {
    return (req, res, next) => {
      next();
    };
  });
});

// 模拟 rateLimit
jest.mock('express-rate-limit', () => {
  return jest.fn(() => {
    return (req, res, next) => {
      next();
    };
  });
});

describe('Security Module', () => {
  beforeEach(() => {
    // 清除所有模拟调用
    jest.clearAllMocks();
  });

  test('should export corsMiddleware', () => {
    expect(corsMiddleware).toBeDefined();
    expect(typeof corsMiddleware).toBe('function');
  });

  test('should export helmetMiddleware', () => {
    expect(helmetMiddleware).toBeDefined();
    expect(typeof helmetMiddleware).toBe('function');
  });

  test('should export rateLimitMiddleware', () => {
    expect(rateLimitMiddleware).toBeDefined();
    expect(typeof rateLimitMiddleware).toBe('function');
  });

  describe('authMiddleware', () => {
    test('should call next function', () => {
      const req = {};
      const res = {};
      const next = jest.fn();

      authMiddleware(req, res, next);
      expect(next).toHaveBeenCalled();
    });
  });

  describe('permissionMiddleware', () => {
    test('should return a middleware function', () => {
      const middleware = permissionMiddleware('test-permission');
      expect(typeof middleware).toBe('function');
    });

    test('should call next function', () => {
      const middleware = permissionMiddleware('test-permission');
      const req = {};
      const res = {};
      const next = jest.fn();

      middleware(req, res, next);
      expect(next).toHaveBeenCalled();
    });
  });
});
