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
    expect(config.rateLimit).toBeDefined();
    expect(config.services).toBeDefined();
    expect(config.health).toBeDefined();
    expect(config.service).toBeDefined();
  });

  test('should have correct default values', () => {
    expect(config.server.port).toBe(8080);
    expect(config.server.timeout).toBe(30000);
    expect(config.security.cors.origin).toBe('*');
    expect(config.security.helmet.enabled).toBe(true);
    expect(config.logging.level).toBe('info');
    expect(config.logging.format).toBe('combined');
    expect(config.logging.enabled).toBe(true);
    expect(config.rateLimit.enabled).toBe(true);
    expect(config.rateLimit.windowMs).toBe(15 * 60 * 1000);
    expect(config.rateLimit.max).toBe(100);
    expect(config.rateLimit.standardHeaders).toBe(true);
    expect(config.rateLimit.legacyHeaders).toBe(false);
    expect(config.health.enabled).toBe(true);
    expect(config.health.endpoint).toBe('/health');
    expect(config.health.interval).toBe(30000);
    expect(config.service.name).toBe('api-gateway');
    expect(config.service.version).toBe('1.0.0');
  });

  test('should have services configuration', () => {
    expect(config.services.backendCore).toBeDefined();
    expect(config.services.decisionService).toBeDefined();
    expect(config.services.edgeComputing).toBeDefined();
    expect(config.services.blockchain).toBeDefined();
    expect(config.services.monitoringService).toBeDefined();
  });

  test('should have correct service default values', () => {
    expect(config.services.backendCore.url).toBe('http://localhost:8001');
    expect(config.services.backendCore.path).toBe('/api/core');
    expect(config.services.backendCore.healthEndpoint).toBe('/health');
    expect(config.services.decisionService.url).toBe('http://localhost:8002');
    expect(config.services.edgeComputing.url).toBe('http://localhost:8003');
    expect(config.services.blockchain.url).toBe('http://localhost:8004');
    expect(config.services.monitoringService.url).toBe('http://localhost:8005');
  });
});
