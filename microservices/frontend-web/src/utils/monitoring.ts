// 前端监控模块

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  type: string;
  context?: Record<string, any>;
}

interface ApiCallMetric {
  endpoint: string;
  method: string;
  status: number;
  duration: number;
  timestamp: number;
  error?: string;
}

interface ErrorMetric {
  message: string;
  stack?: string;
  component?: string;
  timestamp: number;
  context?: Record<string, any>;
}

class FrontendMonitor {
  private metrics: PerformanceMetric[] = [];
  private apiCalls: ApiCallMetric[] = [];
  private errors: ErrorMetric[] = [];
  private flushInterval: number = 30000; // 30秒
  private isInitialized: boolean = false;

  // 初始化监控
  initialize() {
    if (this.isInitialized) return;

    this.isInitialized = true;

    // 监听页面加载性能
    this.monitorPageLoad();

    // 监听路由变化
    this.monitorRouteChanges();

    // 监听错误
    this.monitorErrors();

    // 定期上报指标
    setInterval(() => this.flushMetrics(), this.flushInterval);

    console.log('Frontend monitoring initialized');
  }

  // 监控页面加载性能
  private monitorPageLoad() {
    if (typeof window !== 'undefined' && window.performance) {
      window.addEventListener('load', () => {
        const navigationTiming = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigationTiming) {
          this.addPerformanceMetric('page_load_time', navigationTiming.loadEventEnd - navigationTiming.navigationStart, 'navigation');
          this.addPerformanceMetric('dom_content_loaded_time', navigationTiming.domContentLoadedEventEnd - navigationTiming.navigationStart, 'navigation');
          this.addPerformanceMetric('first_paint', (performance.getEntriesByName('first-paint')[0] as PerformancePaintTiming)?.startTime || 0, 'paint');
          this.addPerformanceMetric('first_contentful_paint', (performance.getEntriesByName('first-contentful-paint')[0] as PerformancePaintTiming)?.startTime || 0, 'paint');
        }
      });
    }
  }

  // 监控路由变化
  private monitorRouteChanges() {
    // 这里可以集成react-router的路由变化监控
    // 例如使用useEffect监听location变化
  }

  // 监控错误
  private monitorErrors() {
    if (typeof window !== 'undefined') {
      // 监听全局错误
      window.addEventListener('error', (event) => {
        this.addError({
          message: event.message,
          stack: event.error?.stack,
          context: {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
          }
        });
      });

      // 监听未捕获的Promise拒绝
      window.addEventListener('unhandledrejection', (event) => {
        this.addError({
          message: event.reason?.message || 'Unhandled Promise rejection',
          stack: event.reason?.stack,
          context: {
            reason: event.reason
          }
        });
      });
    }
  }

  // 添加性能指标
  addPerformanceMetric(name: string, value: number, type: string, context?: Record<string, any>) {
    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      type,
      context
    };

    this.metrics.push(metric);
    console.debug('Performance metric added:', metric);
  }

  // 添加API调用指标
  addApiCall(endpoint: string, method: string, status: number, duration: number, error?: string) {
    const apiCall: ApiCallMetric = {
      endpoint,
      method,
      status,
      duration,
      timestamp: Date.now(),
      error
    };

    this.apiCalls.push(apiCall);
    console.debug('API call added:', apiCall);
  }

  // 添加错误
  addError(error: Partial<ErrorMetric>) {
    const errorMetric: ErrorMetric = {
      message: error.message || 'Unknown error',
      stack: error.stack,
      component: error.component,
      timestamp: Date.now(),
      context: error.context
    };

    this.errors.push(errorMetric);
    console.error('Error captured:', errorMetric);
  }

  // 上报指标
  private async flushMetrics() {
    if (this.metrics.length === 0 && this.apiCalls.length === 0 && this.errors.length === 0) {
      return;
    }

    const metricsToSend = {
      performance: this.metrics,
      apiCalls: this.apiCalls,
      errors: this.errors,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      referrer: document.referrer
    };

    try {
      // 这里可以发送到监控服务
      // 暂时只在控制台打印
      console.log('Flushing metrics:', metricsToSend);

      // 清空指标
      this.metrics = [];
      this.apiCalls = [];
      this.errors = [];
    } catch (error) {
      console.error('Error flushing metrics:', error);
    }
  }

  // 获取当前指标
  getMetrics() {
    return {
      performance: [...this.metrics],
      apiCalls: [...this.apiCalls],
      errors: [...this.errors]
    };
  }

  // 手动上报指标
  async flush() {
    await this.flushMetrics();
  }
}

// 导出单例实例
export const frontendMonitor = new FrontendMonitor();

// 导出监控钩子
export const useMonitor = () => {
  return {
    addPerformanceMetric: frontendMonitor.addPerformanceMetric.bind(frontendMonitor),
    addApiCall: frontendMonitor.addApiCall.bind(frontendMonitor),
    addError: frontendMonitor.addError.bind(frontendMonitor),
    getMetrics: frontendMonitor.getMetrics.bind(frontendMonitor),
    flush: frontendMonitor.flush.bind(frontendMonitor)
  };
};

// 导出用于API调用的包装函数
export const monitoredFetch = async (url: string, options: RequestInit = {}) => {
  const start = Date.now();
  const method = options.method || 'GET';

  try {
    const response = await fetch(url, options);
    const duration = Date.now() - start;

    frontendMonitor.addApiCall(url, method, response.status, duration);

    return response;
  } catch (error) {
    const duration = Date.now() - start;
    frontendMonitor.addApiCall(url, method, 0, duration, error instanceof Error ? error.message : 'Unknown error');
    throw error;
  }
};
