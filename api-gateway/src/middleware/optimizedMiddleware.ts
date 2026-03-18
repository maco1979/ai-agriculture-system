import { Request, Response, NextFunction } from 'express';

interface MiddlewareConfig {
  logging: boolean;
  metrics: boolean;
  auth: boolean;
  errorHandling: boolean;
}

class OptimizedMiddleware {
  private config: MiddlewareConfig;
  private requestCounter: number = 0;
  private errorCounter: number = 0;

  constructor(config: Partial<MiddlewareConfig> = {}) {
    this.config = {
      logging: config.logging ?? true,
      metrics: config.metrics ?? true,
      auth: config.auth ?? true,
      errorHandling: config.errorHandling ?? true
    };
  }

  // 综合中间件
  public async handle(req: Request, res: Response, next: NextFunction): Promise<void> {
    const requestId = ++this.requestCounter;
    const startTime = Date.now();

    try {
      // 认证处理
      if (this.config.auth) {
        const authResult = this.handleAuth(req, res);
        if (!authResult) {
          return;
        }
      }

      // 请求处理前的日志
      if (this.config.logging) {
        this.logRequestStart(req, requestId);
      }

      // 监听响应完成事件
      res.on('finish', () => {
        const duration = Date.now() - startTime;
        const statusCode = res.statusCode;

        // 响应完成后的日志
        if (this.config.logging) {
          this.logRequestEnd(req, res, duration, requestId);
        }

        // 记录指标
        if (this.config.metrics) {
          this.recordMetrics(req, res, duration, statusCode);
        }

        // 错误计数
        if (statusCode >= 400) {
          this.errorCounter++;
        }
      });

      // 继续处理请求
      await next();
    } catch (error) {
      // 错误处理
      if (this.config.errorHandling) {
        this.handleError(error, req, res, next);
      } else {
        next(error);
      }
    }
  }

  // 认证处理
  private handleAuth(req: Request, res: Response): boolean {
    // 放行预检请求
    if (req.method === 'OPTIONS') {
      return true;
    }

    // 简单的API密钥认证
    const apiKey = req.headers['x-api-key'];

    if (!apiKey) {
      res.status(401).json({
        error: '未提供API密钥',
        message: '请在请求头中提供有效的X-API-KEY'
      });
      return false;
    }

    // 在实际应用中，这里应该验证API密钥的有效性
    const validApiKeys = ['your-api-key-here', 'default-api-key'];

    if (!validApiKeys.includes(apiKey as string)) {
      res.status(403).json({
        error: '无效的API密钥',
        message: '提供的API密钥无效'
      });
      return false;
    }

    return true;
  }

  // 错误处理
  private handleError(error: any, req: Request, res: Response, next: NextFunction): void {
    console.error('API网关错误:', error);

    // 处理不同类型的错误
    if (error.code === 'ECONNREFUSED') {
      res.status(503).json({
        error: '服务不可用',
        message: '后端服务暂时不可用，请稍后重试'
      });
      return;
    }

    if (error.response && error.response.status) {
      // 代理错误
      res.status(error.response.status).json({
        error: '后端服务错误',
        message: error.response.data?.message || '后端服务处理错误'
      });
      return;
    }

    if (error.statusCode) {
      // 自定义错误
      res.status(error.statusCode).json({
        error: error.error || '请求错误',
        message: error.message || '请求处理错误'
      });
      return;
    }

    // 默认错误处理
    res.status(500).json({
      error: '内部服务器错误',
      message: '服务器遇到意外错误'
    });
  }

  // 记录请求开始
  private logRequestStart(req: Request, requestId: number): void {
    console.log(`[${new Date().toISOString()}] [${requestId}] ${req.method} ${req.path} - 开始处理`);
  }

  // 记录请求结束
  private logRequestEnd(req: Request, res: Response, duration: number, requestId: number): void {
    console.log(`[${new Date().toISOString()}] [${requestId}] ${req.method} ${req.path} - ${res.statusCode} - ${duration}ms`);
  }

  // 记录指标
  private recordMetrics(req: Request, res: Response, duration: number, statusCode: number): void {
    // 在实际应用中，这里应该将指标发送到Prometheus或其他监控系统
    console.log(`METRICS: ${req.method} ${req.path} - ${statusCode} - ${duration}ms`);
  }

  // 获取中间件状态
  public getStatus(): {
    requestCount: number;
    errorCount: number;
    errorRate: number;
    config: MiddlewareConfig;
  } {
    return {
      requestCount: this.requestCounter,
      errorCount: this.errorCounter,
      errorRate: this.requestCounter > 0 ? this.errorCounter / this.requestCounter : 0,
      config: this.config
    };
  }

  // 更新配置
  public updateConfig(config: Partial<MiddlewareConfig>): void {
    this.config = {
      ...this.config,
      ...config
    };
    console.log('🔧 中间件配置已更新:', this.config);
  }
}

// 导出单例实例
export const optimizedMiddleware = new OptimizedMiddleware();

// 导出中间件函数
export const middlewareHandler = optimizedMiddleware.handle.bind(optimizedMiddleware);

// 导出状态获取函数
export const getMiddlewareStatus = optimizedMiddleware.getStatus.bind(optimizedMiddleware);

// 导出配置更新函数
export const updateMiddlewareConfig = optimizedMiddleware.updateConfig.bind(optimizedMiddleware);
