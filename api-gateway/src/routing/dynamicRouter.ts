import { Request, Response, NextFunction } from 'express';
import { createProxyMiddleware, Options } from 'http-proxy-middleware';
import { loadBalancer } from '../load-balancing/loadBalancer.js';

interface ServiceConfig {
  baseUrl: string;
  prefix: string;
  healthCheck: string;
  weight?: number;
}

interface RouteConfig {
  prefix: string;
  service: string;
  enabled: boolean;
  priority: number;
}

class DynamicRouter {
  private serviceConfigs: Map<string, ServiceConfig> = new Map();
  private routeConfigs: RouteConfig[] = [];
  private proxyCache: Map<string, any> = new Map();
  private routeStats: Map<string, {
    requestCount: number;
    errorCount: number;
    avgResponseTime: number;
    lastAccess: Date;
  }> = new Map();

  // 注册服务配置
  public registerService(name: string, config: ServiceConfig): void {
    this.serviceConfigs.set(name, config);
    console.log(`✅ 注册服务配置: ${name} -> ${config.baseUrl}`);
  }

  // 注册路由配置
  public registerRoute(config: RouteConfig): void {
    const existingIndex = this.routeConfigs.findIndex(r => r.prefix === config.prefix);
    if (existingIndex >= 0) {
      this.routeConfigs[existingIndex] = config;
    } else {
      this.routeConfigs.push(config);
    }
    // 按优先级排序，优先级高的在前
    this.routeConfigs.sort((a, b) => b.priority - a.priority);
    console.log(`✅ 注册路由配置: ${config.prefix} -> ${config.service}`);
  }

  // 获取目标服务配置
  public getTargetService(req: Request): { service: string; config: ServiceConfig } | null {
    const path = req.path;
    
    // 查找匹配的路由配置
    for (const route of this.routeConfigs) {
      if (route.enabled && path.startsWith(route.prefix)) {
        const config = this.serviceConfigs.get(route.service);
        if (config) {
          // 更新路由统计信息
          this.updateRouteStats(route.prefix, false, 0);
          return { service: route.service, config };
        }
      }
    }
    
    return null;
  }

  // 构建目标URL
  public buildTargetUrl(req: Request, service: string, config: ServiceConfig): string {
    // 使用负载均衡器选择实例
    const instances = loadBalancer.getServiceInstances(service);
    if (instances && instances.length > 0) {
      const instance = loadBalancer.selectInstance(service, instances);
      if (instance) {
        // 更新连接计数
        loadBalancer.incrementConnections(service, instance.id);
        
        // 构建目标URL
        const baseUrl = `http://${instance.host}:${instance.port}`;
        return `${baseUrl}${req.path}`;
      }
    }
    
    // 如果没有可用实例，使用默认配置
    return `${config.baseUrl}${req.path}`;
  }

  // 创建代理中间件
  public createProxy(service: string, config: ServiceConfig): any {
    const cacheKey = `${service}:${config.baseUrl}`;
    if (this.proxyCache.has(cacheKey)) {
      return this.proxyCache.get(cacheKey);
    }

    const proxyOptions: Options = {
      target: config.baseUrl,
      changeOrigin: true,
      logLevel: 'debug',
      onProxyReq: (proxyReq, req, res) => {
        // 可以在这里添加自定义逻辑
      },
      onProxyRes: (proxyRes, req, res) => {
        // 可以在这里添加自定义逻辑
        const service = this.getServiceFromRequest(req);
        if (service) {
          const instanceId = this.getInstanceIdFromRequest(req);
          if (instanceId) {
            // 减少连接计数
            loadBalancer.decrementConnections(service, instanceId);
          }
        }
      },
      onError: (err, req, res) => {
        console.error('代理错误:', err);
        const route = this.getRouteFromRequest(req);
        if (route) {
          this.updateRouteStats(route, true, 0);
        }
        res.status(500).json({ error: '服务暂时不可用' });
      }
    };

    const proxy = createProxyMiddleware(proxyOptions);
    this.proxyCache.set(cacheKey, proxy);
    return proxy;
  }

  // 路由中间件
  public async routeMiddleware(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const start = Date.now();
      
      // 获取目标服务
      const target = this.getTargetService(req);
      if (!target) {
        return res.status(404).json({ error: '路由未找到' });
      }

      const { service, config } = target;
      
      // 检查服务健康状态
      const isHealthy = await this.checkServiceHealth(service, config);
      if (!isHealthy) {
        return res.status(503).json({ error: '服务暂时不可用' });
      }

      // 创建或获取代理
      const proxy = this.createProxy(service, config);
      
      // 记录请求开始时间
      req.headers['x-request-start'] = start.toString();
      
      // 处理请求
      proxy(req, res, (err) => {
        if (err) {
          console.error('路由错误:', err);
          const route = this.getRouteFromRequest(req);
          if (route) {
            this.updateRouteStats(route, true, Date.now() - start);
          }
          next(err);
        } else {
          const route = this.getRouteFromRequest(req);
          if (route) {
            this.updateRouteStats(route, false, Date.now() - start);
          }
        }
      });
    } catch (error) {
      console.error('路由中间件错误:', error);
      next(error);
    }
  }

  // 检查服务健康状态
  private async checkServiceHealth(service: string, config: ServiceConfig): Promise<boolean> {
    try {
      // 这里可以实现更复杂的健康检查逻辑
      // 例如，发送HTTP请求到健康检查端点
      // 暂时返回true，后续可以集成到服务发现模块
      return true;
    } catch (error) {
      console.error(`服务健康检查失败: ${service}`, error);
      return false;
    }
  }

  // 更新路由统计信息
  private updateRouteStats(route: string, isError: boolean, responseTime: number): void {
    const stats = this.routeStats.get(route) || {
      requestCount: 0,
      errorCount: 0,
      avgResponseTime: 0,
      lastAccess: new Date()
    };

    stats.requestCount++;
    if (isError) {
      stats.errorCount++;
    }
    // 简单的移动平均计算
    stats.avgResponseTime = (stats.avgResponseTime * (stats.requestCount - 1) + responseTime) / stats.requestCount;
    stats.lastAccess = new Date();

    this.routeStats.set(route, stats);

    // 可以在这里添加自动调整逻辑
    // 例如，如果错误率过高，自动禁用路由或调整优先级
    if (stats.requestCount > 100 && stats.errorCount / stats.requestCount > 0.1) {
      console.warn(`⚠️  路由 ${route} 错误率过高: ${(stats.errorCount / stats.requestCount * 100).toFixed(2)}%`);
      // 这里可以添加自动调整逻辑
    }
  }

  // 从请求中获取服务名称
  private getServiceFromRequest(req: Request): string | null {
    // 这里需要根据实际情况实现
    // 暂时返回null
    return null;
  }

  // 从请求中获取实例ID
  private getInstanceIdFromRequest(req: Request): string | null {
    // 这里需要根据实际情况实现
    // 暂时返回null
    return null;
  }

  // 从请求中获取路由前缀
  private getRouteFromRequest(req: Request): string | null {
    const path = req.path;
    for (const route of this.routeConfigs) {
      if (path.startsWith(route.prefix)) {
        return route.prefix;
      }
    }
    return null;
  }

  // 获取路由统计信息
  public getRouteStats(): any {
    return Object.fromEntries(this.routeStats);
  }

  // 获取服务配置
  public getServiceConfigs(): any {
    return Object.fromEntries(this.serviceConfigs);
  }

  // 获取路由配置
  public getRouteConfigs(): RouteConfig[] {
    return this.routeConfigs;
  }

  // 启用/禁用路由
  public setRouteEnabled(prefix: string, enabled: boolean): void {
    const route = this.routeConfigs.find(r => r.prefix === prefix);
    if (route) {
      route.enabled = enabled;
      console.log(`🔧 路由 ${prefix} 已${enabled ? '启用' : '禁用'}`);
    }
  }

  // 调整路由优先级
  public setRoutePriority(prefix: string, priority: number): void {
    const route = this.routeConfigs.find(r => r.prefix === prefix);
    if (route) {
      route.priority = priority;
      // 重新排序
      this.routeConfigs.sort((a, b) => b.priority - a.priority);
      console.log(`🔧 路由 ${prefix} 优先级已调整为 ${priority}`);
    }
  }
}

export const dynamicRouter = new DynamicRouter();
