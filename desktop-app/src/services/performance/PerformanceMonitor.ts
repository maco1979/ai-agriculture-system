// 性能监控服务

class PerformanceMonitor {
  private metrics: Map<string, { start: number; end: number | null; value: number | null }> = new Map();
  private fpsHistory: number[] = [];
  private memoryHistory: { used: number; total: number; timestamp: number }[] = [];
  private networkRequests: Array<{ url: string; method: string; duration: number; status: number; timestamp: number }> = [];
  private maxHistorySize: number = 100;

  // 开始计时
  start(name: string) {
    this.metrics.set(name, {
      start: performance.now(),
      end: null,
      value: null
    });
  }

  // 结束计时
  end(name: string) {
    const metric = this.metrics.get(name);
    if (metric) {
      const end = performance.now();
      const value = end - metric.start;
      this.metrics.set(name, {
        ...metric,
        end,
        value
      });
      return value;
    }
    return null;
  }

  // 获取指标值
  getMetric(name: string) {
    const metric = this.metrics.get(name);
    return metric?.value || null;
  }

  // 清除指标
  clearMetric(name: string) {
    this.metrics.delete(name);
  }

  // 清除所有指标
  clearAllMetrics() {
    this.metrics.clear();
  }

  // 获取FPS
  getFPS() {
    return this.calculateFPS();
  }

  // 计算FPS
  private calculateFPS() {
    const now = performance.now();
    const fps = 60; // 假设60fps
    
    // 限制历史记录大小
    if (this.fpsHistory.length >= this.maxHistorySize) {
      this.fpsHistory.shift();
    }
    
    this.fpsHistory.push(fps);
    
    // 计算平均FPS
    const averageFPS = this.fpsHistory.reduce((sum, value) => sum + value, 0) / this.fpsHistory.length;
    return averageFPS;
  }

  // 记录内存使用
  recordMemoryUsage(used: number, total: number) {
    const timestamp = Date.now();
    
    // 限制历史记录大小
    if (this.memoryHistory.length >= this.maxHistorySize) {
      this.memoryHistory.shift();
    }
    
    this.memoryHistory.push({ used, total, timestamp });
  }

  // 记录网络请求
  recordNetworkRequest(url: string, method: string, duration: number, status: number) {
    const timestamp = Date.now();
    
    // 限制历史记录大小
    if (this.networkRequests.length >= this.maxHistorySize) {
      this.networkRequests.shift();
    }
    
    this.networkRequests.push({ url, method, duration, status, timestamp });
  }

  // 获取性能报告
  getPerformanceReport() {
    const metrics = Object.fromEntries(this.metrics.entries());
    const averageFPS = this.calculateFPS();
    const latestMemory = this.memoryHistory[this.memoryHistory.length - 1];
    const networkStats = this.getNetworkStats();

    return {
      metrics,
      fps: {
        current: averageFPS,
        history: this.fpsHistory
      },
      memory: {
        latest: latestMemory,
        history: this.memoryHistory
      },
      network: {
        requests: this.networkRequests,
        stats: networkStats
      },
      timestamp: Date.now()
    };
  }

  // 获取网络请求统计
  private getNetworkStats() {
    const totalRequests = this.networkRequests.length;
    const successfulRequests = this.networkRequests.filter(req => req.status >= 200 && req.status < 300).length;
    const averageDuration = this.networkRequests.reduce((sum, req) => sum + req.duration, 0) / totalRequests || 0;

    return {
      totalRequests,
      successfulRequests,
      successRate: totalRequests > 0 ? (successfulRequests / totalRequests) * 100 : 0,
      averageDuration
    };
  }

  // 启动实时监控
  startRealTimeMonitoring(interval: number = 1000) {
    const monitoringInterval = setInterval(() => {
      // 记录FPS
      this.calculateFPS();

      // 记录内存使用（如果在浏览器环境中）
      if (typeof window !== 'undefined' && (window as any).performance && (window as any).performance.memory) {
        const memory = (window as any).performance.memory;
        this.recordMemoryUsage(memory.usedJSHeapSize, memory.totalJSHeapSize);
      }

    }, interval);

    return monitoringInterval;
  }

  // 停止实时监控
  stopRealTimeMonitoring(intervalId: NodeJS.Timeout) {
    clearInterval(intervalId);
  }

  // 分析性能瓶颈
  analyzePerformance() {
    const report = this.getPerformanceReport();
    const bottlenecks: string[] = [];

    // 检查FPS
    if (report.fps.current < 30) {
      bottlenecks.push(`低FPS: ${report.fps.current.toFixed(1)}fps`);
    }

    // 检查内存使用
    if (report.memory.latest) {
      const memoryUsagePercent = (report.memory.latest.used / report.memory.latest.total) * 100;
      if (memoryUsagePercent > 80) {
        bottlenecks.push(`内存使用过高: ${memoryUsagePercent.toFixed(1)}%`);
      }
    }

    // 检查网络请求
    if (report.network.stats.averageDuration > 1000) {
      bottlenecks.push(`网络请求缓慢: ${report.network.stats.averageDuration.toFixed(1)}ms`);
    }

    // 检查指标
    for (const [name, metric] of Object.entries(report.metrics)) {
      if (metric.value && metric.value > 100) {
        bottlenecks.push(`${name}: ${metric.value.toFixed(1)}ms`);
      }
    }

    return {
      report,
      bottlenecks,
      suggestions: this.getPerformanceSuggestions(bottlenecks)
    };
  }

  // 获取性能优化建议
  private getPerformanceSuggestions(bottlenecks: string[]) {
    const suggestions: string[] = [];

    if (bottlenecks.some(b => b.includes('低FPS'))) {
      suggestions.push('优化动画性能，使用requestAnimationFrame');
      suggestions.push('减少重排和重绘，使用CSS transform');
      suggestions.push('避免在渲染过程中进行复杂计算');
    }

    if (bottlenecks.some(b => b.includes('内存使用过高'))) {
      suggestions.push('释放不再使用的资源');
      suggestions.push('使用弱引用存储大对象');
      suggestions.push('优化组件卸载逻辑');
    }

    if (bottlenecks.some(b => b.includes('网络请求缓慢'))) {
      suggestions.push('使用缓存减少重复请求');
      suggestions.push('优化API响应时间');
      suggestions.push('使用批量请求减少网络往返');
    }

    return suggestions;
  }

  // 导出性能报告
  exportReport() {
    const report = this.getPerformanceReport();
    return JSON.stringify(report, null, 2);
  }

  // 清除所有数据
  clear() {
    this.metrics.clear();
    this.fpsHistory = [];
    this.memoryHistory = [];
    this.networkRequests = [];
  }
}

// 全局性能监控实例
export const performanceMonitor = new PerformanceMonitor();

// 性能监控装饰器
export function monitorPerformance(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const originalMethod = descriptor.value;
  
  descriptor.value = function(...args: any[]) {
    const methodName = `${target.constructor.name}.${propertyKey}`;
    performanceMonitor.start(methodName);
    
    try {
      const result = originalMethod.apply(this, args);
      
      if (result instanceof Promise) {
        return result.then((res: any) => {
          performanceMonitor.end(methodName);
          return res;
        }).catch((err: any) => {
          performanceMonitor.end(methodName);
          throw err;
        });
      } else {
        performanceMonitor.end(methodName);
        return result;
      }
    } catch (error) {
      performanceMonitor.end(methodName);
      throw error;
    }
  };
}

// 网络请求监控
export function monitorNetworkRequest(url: string, method: string) {
  const start = performance.now();
  
  return (status: number) => {
    const end = performance.now();
    const duration = end - start;
    
    performanceMonitor.recordNetworkRequest(url, method, duration, status);
    
    return duration;
  };
}

// FPS监控
export function monitorFPS() {
  let frameCount = 0;
  let lastTime = performance.now();
  
  function updateFPS() {
    frameCount++;
    const currentTime = performance.now();
    
    if (currentTime - lastTime >= 1000) {
      const fps = frameCount;
      performanceMonitor['fpsHistory'].push(fps);
      
      // 限制历史记录大小
      if (performanceMonitor['fpsHistory'].length > performanceMonitor['maxHistorySize']) {
        performanceMonitor['fpsHistory'].shift();
      }
      
      frameCount = 0;
      lastTime = currentTime;
    }
    
    requestAnimationFrame(updateFPS);
  }
  
  requestAnimationFrame(updateFPS);
}
