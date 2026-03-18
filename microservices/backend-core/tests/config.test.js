// 保存原始的 NODE_ENV
const originalNodeEnv = process.env.NODE_ENV;

// 直接设置 NODE_ENV 为 development
process.env.NODE_ENV = 'development';

// 导入 config
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
    expect(config.security).toBeDefined();
    expect(config.logging).toBeDefined();
    expect(config.database).toBeDefined();
    expect(config.api).toBeDefined();
    expect(config.health).toBeDefined();
    expect(config.service).toBeDefined();
  });

  test('should have correct default values', () => {
    expect(config.server.port).toBe(8001);
    expect(config.server.timeout).toBe(30000);
    expect(config.security.cors.origin).toBe('*');
    expect(config.security.helmet.enabled).toBe(true);
    expect(config.logging.level).toBe('info');
    expect(config.logging.format).toBe('combined');
    expect(config.logging.enabled).toBe(true);
    expect(config.api.prefix).toBe('/api');
    expect(config.api.version).toBe('v1');
    expect(config.health.enabled).toBe(true);
    expect(config.health.endpoint).toBe('/health');
    expect(config.service.name).toBe('backend-core');
    expect(config.service.version).toBe('1.0.0');
  });
});
