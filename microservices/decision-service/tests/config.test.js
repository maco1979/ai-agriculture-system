// 保存原始的 NODE_ENV
const originalNodeEnv = process.env.NODE_ENV;

// 直接设置 NODE_ENV 为 development
process.env.NODE_ENV = 'development';

import config from '../src/config/config.js';

// 在测试结束后恢复原始的 NODE_ENV
afterAll(() => {
  process.env.NODE_ENV = originalNodeEnv;
});

describe('Config Module', () => {
  test('should load configuration', () => {
    expect(config).toBeDefined();
    expect(typeof config).toBe('object');
  });

  test('should have required configuration properties', () => {
    expect(config.server).toBeDefined();
    expect(config.api).toBeDefined();
    expect(config.security).toBeDefined();
    expect(config.logging).toBeDefined();
    expect(config.health).toBeDefined();
    expect(config.service).toBeDefined();
    expect(config.database).toBeDefined();
  });

  test('should have correct default values', () => {
    expect(config.server.port).toBe(8002);
    expect(config.server.host).toBe('0.0.0.0');
    expect(config.api.prefix).toBe('/api/decision');
    expect(config.security.cors.origin).toBe('*');
    expect(config.logging.level).toBe('info');
    expect(config.logging.format).toBe('combined');
    expect(config.logging.enabled).toBe(true);
    expect(config.health.enabled).toBe(true);
    expect(config.health.endpoint).toBe('/health');
    expect(config.health.interval).toBe(30000);
    expect(config.service.name).toBe('decision-service');
    expect(config.service.version).toBe('1.0.0');
    expect(config.service.description).toBe('Decision service for AI-powered decision making');
  });

  test('should have correct database default values', () => {
    expect(config.database.uri).toBe('mongodb://localhost:27017/decision-service');
    expect(config.database.options).toBeDefined();
    expect(config.database.options.useNewUrlParser).toBe(true);
    expect(config.database.options.useUnifiedTopology).toBe(true);
  });
});
