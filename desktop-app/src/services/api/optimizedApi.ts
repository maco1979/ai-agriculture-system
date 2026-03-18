import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { useSettingsStore } from '@/store';

// 请求缓存接口
interface RequestCache {
  [key: string]: {
    data: any;
    timestamp: number;
    ttl: number;
  };
}

// 批量请求接口
interface BatchRequest {
  id: string;
  config: AxiosRequestConfig;
  resolve: (value: any) => void;
  reject: (reason: any) => void;
}

// API配置接口
interface ApiConfig {
  baseURL: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
  cacheEnabled: boolean;
  cacheTTL: number;
  batchEnabled: boolean;
  batchDelay: number;
}

// 优化的API客户端类
class OptimizedApiClient {
  private axios: AxiosInstance;
  private config: ApiConfig;
  private requestCache: RequestCache = {};
  private batchRequests: BatchRequest[] = [];
  private batchTimer: NodeJS.Timeout | null = null;
  private pendingRequests: Map<string, Promise<any>> = new Map();

  constructor(config: Partial<ApiConfig> = {}) {
    const defaultConfig: ApiConfig = {
      baseURL: '',
      timeout: 30000,
      retryAttempts: 3,
      retryDelay: 1000,
      cacheEnabled: true,
      cacheTTL: 60000, // 1分钟
      batchEnabled: true,
      batchDelay: 100, // 100ms
    };

    this.config = { ...defaultConfig, ...config };

    // 创建axios实例
    this.axios = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.axios.interceptors.request.use(
      (config) => {
        // 从设置中获取最新配置
        const settingsStore = useSettingsStore.getState();
        if (settingsStore) {
          config.timeout = settingsStore.networkSettings.timeout;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.axios.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        return this.handleError(error);
      }
    );
  }

  // 生成请求缓存键
  private generateCacheKey(config: AxiosRequestConfig): string {
    if (config.method !== 'get') return '';
    const url = config.baseURL ? config.baseURL + config.url : config.url;
    const params = config.params ? JSON.stringify(config.params) : '';
    return `${url}?${params}`;
  }

  // 检查缓存
  private checkCache(config: AxiosRequestConfig): any {
    if (!this.config.cacheEnabled || config.method !== 'get') return null;
    
    const cacheKey = this.generateCacheKey(config);
    if (!cacheKey) return null;
    
    const cachedItem = this.requestCache[cacheKey];
    if (!cachedItem) return null;
    
    const now = Date.now();
    if (now - cachedItem.timestamp < cachedItem.ttl) {
      return cachedItem.data;
    } else {
      // 缓存过期，删除
      delete this.requestCache[cacheKey];
      return null;
    }
  }

  // 设置缓存
  private setCache(config: AxiosRequestConfig, data: any): void {
    if (!this.config.cacheEnabled || config.method !== 'get') return;
    
    const cacheKey = this.generateCacheKey(config);
    if (!cacheKey) return;
    
    this.requestCache[cacheKey] = {
      data,
      timestamp: Date.now(),
      ttl: this.config.cacheTTL,
    };
  }

  // 批量处理请求
  private addToBatch(config: AxiosRequestConfig): Promise<any> {
    return new Promise((resolve, reject) => {
      const requestId = `${config.method}:${config.url}`;
      this.batchRequests.push({
        id: requestId,
        config,
        resolve,
        reject,
      });

      // 启动批处理定时器
      if (!this.batchTimer) {
        this.batchTimer = setTimeout(() => {
          this.processBatch();
        }, this.config.batchDelay);
      }
    });
  }

  // 处理批处理
  private async processBatch(): Promise<void> {
    if (this.batchRequests.length === 0) return;

    const requests = [...this.batchRequests];
    this.batchRequests = [];
    this.batchTimer = null;

    // 按URL分组请求
    const groupedRequests = requests.reduce((groups, request) => {
      const url = request.config.url || '';
      if (!groups[url]) {
        groups[url] = [];
      }
      groups[url].push(request);
      return groups;
    }, {} as { [key: string]: BatchRequest[] });

    // 处理每组请求
    for (const [_url, group] of Object.entries(groupedRequests)) {
      try {
        // 对于GET请求，合并参数
        if (group[0].config.method === 'get') {
          const params = group.reduce((mergedParams, request) => {
            return { ...mergedParams, ...request.config.params };
          }, {});

          const response = await this.axios({
            ...group[0].config,
            params,
          });

          // 分发响应
          group.forEach(request => {
            request.resolve(response.data);
            this.setCache(request.config, response.data);
          });
        } else {
          // 对于其他请求，逐个处理
          for (const request of group) {
            try {
              const response = await this.axios(request.config);
              request.resolve(response.data);
            } catch (error) {
              request.reject(error);
            }
          }
        }
      } catch (error) {
        // 分发错误
        group.forEach(request => {
          request.reject(error);
        });
      }
    }
  }

  // 处理错误
  private async handleError(error: AxiosError): Promise<any> {
    const config = error.config as AxiosRequestConfig & { _retry?: boolean; _retryCount?: number };
    
    // 检查是否需要重试
    if (config && !config._retry && config._retryCount !== undefined && config._retryCount < this.config.retryAttempts) {
      config._retry = true;
      config._retryCount = (config._retryCount || 0) + 1;

      // 指数退避
      const delay = this.config.retryDelay * Math.pow(2, config._retryCount - 1);
      
      await new Promise(resolve => setTimeout(resolve, delay));
      return this.axios(config);
    }

    return Promise.reject(error);
  }

  // 通用请求方法
  async request<T = any>(config: AxiosRequestConfig): Promise<T> {
    // 检查缓存
    const cachedData = this.checkCache(config);
    if (cachedData) {
      return cachedData;
    }

    // 检查是否有相同请求正在进行
    const requestKey = `${config.method}:${config.url}:${JSON.stringify(config.params)}`;
    if (this.pendingRequests.has(requestKey)) {
      return this.pendingRequests.get(requestKey);
    }

    // 创建请求Promise
    const requestPromise = new Promise<T>(async (resolve, reject) => {
      try {
        // 检查是否需要批处理
        if (this.config.batchEnabled && config.method === 'get') {
          const batchResult = await this.addToBatch(config);
          resolve(batchResult);
        } else {
          // 直接发送请求
          const response = await this.axios(config);
          this.setCache(config, response.data);
          resolve(response.data);
        }
      } catch (error) {
        reject(error);
      } finally {
        // 移除挂起的请求
        this.pendingRequests.delete(requestKey);
      }
    });

    // 记录挂起的请求
    this.pendingRequests.set(requestKey, requestPromise);

    return requestPromise;
  }

  // GET请求
  async get<T = any>(url: string, config: AxiosRequestConfig = {}): Promise<T> {
    return this.request<T>({ ...config, method: 'get', url });
  }

  // POST请求
  async post<T = any>(url: string, data?: any, config: AxiosRequestConfig = {}): Promise<T> {
    return this.request<T>({ ...config, method: 'post', url, data });
  }

  // PUT请求
  async put<T = any>(url: string, data?: any, config: AxiosRequestConfig = {}): Promise<T> {
    return this.request<T>({ ...config, method: 'put', url, data });
  }

  // DELETE请求
  async delete<T = any>(url: string, config: AxiosRequestConfig = {}): Promise<T> {
    return this.request<T>({ ...config, method: 'delete', url });
  }

  // 清除缓存
  clearCache(): void {
    this.requestCache = {};
  }

  // 清除特定缓存
  clearCacheByUrl(url: string): void {
    for (const key in this.requestCache) {
      if (key.includes(url)) {
        delete this.requestCache[key];
      }
    }
  }

  // 获取缓存大小
  getCacheSize(): number {
    return Object.keys(this.requestCache).length;
  }
}

// 创建全局实例
const optimizedApiClient = new OptimizedApiClient();

export { OptimizedApiClient, optimizedApiClient };
export default optimizedApiClient;
