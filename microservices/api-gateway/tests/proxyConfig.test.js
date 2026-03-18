// 保存原始的 NODE_ENV
const originalNodeEnv = process.env.NODE_ENV;

// 直接设置 NODE_ENV 为 development
process.env.NODE_ENV = 'development';

import { getProxyConfigs, getServiceProxyConfig } from '../src/proxy/proxyConfig.js';
import { formatProxyConfig } from '../src/utils/utils.js';

// 在测试结束后恢复原始的 NODE_ENV
afterAll(() => {
  process.env.NODE_ENV = originalNodeEnv;
});

// 模拟 formatProxyConfig
jest.mock('../src/utils/utils.js', () => {
  return {
    formatProxyConfig: jest.fn((service) => {
      return {
        target: service.url,
        changeOrigin: true,
        pathRewrite: {
          [`^${service.path}`]: ''
        }
      };
    })
  };
});

describe('Proxy Config Module', () => {
  beforeEach(() => {
    // 清除所有模拟调用
    jest.clearAllMocks();
  });

  test('should return proxy configs for all services', () => {
    const proxyConfigs = getProxyConfigs();
    expect(proxyConfigs).toBeDefined();
    expect(typeof proxyConfigs).toBe('object');
    expect(Object.keys(proxyConfigs).length).toBeGreaterThan(0);
    expect(formatProxyConfig).toHaveBeenCalled();
  });

  test('should return service proxy config for existing service', () => {
    const serviceName = 'backendCore';
    const serviceProxyConfig = getServiceProxyConfig(serviceName);
    expect(serviceProxyConfig).toBeDefined();
    expect(serviceProxyConfig.path).toBeDefined();
    expect(serviceProxyConfig.config).toBeDefined();
    expect(formatProxyConfig).toHaveBeenCalled();
  });

  test('should throw error for non-existing service', () => {
    const serviceName = 'nonExistingService';
    expect(() => {
      getServiceProxyConfig(serviceName);
    }).toThrow(`Service ${serviceName} not found in configuration`);
  });
});
