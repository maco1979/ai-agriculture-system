import config from '../config/config.js';
import { formatProxyConfig } from '../utils/utils.js';

// 生成所有服务的代理配置
const generateProxyConfigs = () => {
  const proxyConfigs = {};
  
  Object.entries(config.services).forEach(([key, service]) => {
    proxyConfigs[key] = {
      path: service.path,
      config: formatProxyConfig(service)
    };
  });
  
  return proxyConfigs;
};

// 获取所有服务的代理配置
const getProxyConfigs = () => {
  return generateProxyConfigs();
};

// 获取单个服务的代理配置
const getServiceProxyConfig = (serviceName) => {
  const service = config.services[serviceName];
  if (!service) {
    throw new Error(`Service ${serviceName} not found in configuration`);
  }
  
  return {
    path: service.path,
    config: formatProxyConfig(service)
  };
};

export {
  getProxyConfigs,
  getServiceProxyConfig
};