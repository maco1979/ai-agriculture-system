import React from 'react';
import { apiClient } from '@/services/api';

// 请求合并缓存
const requestCache = new Map<string, Promise<any>>();

// 请求并发控制
const concurrencyLimit = 6;
const activeRequests = new Set<string>();
const requestQueue: (() => Promise<any>)[] = [];

// 生成请求缓存键
function generateRequestKey(endpoint: string, method: string, params?: any): string {
  const keyParts = [method, endpoint];
  if (params) {
    try {
      keyParts.push(JSON.stringify(params));
    } catch (error) {
      // 忽略无法序列化的参数
    }
  }
  return keyParts.join('|');
}

// 执行排队的请求
function processRequestQueue() {
  if (activeRequests.size < concurrencyLimit && requestQueue.length > 0) {
    const nextRequest = requestQueue.shift();
    if (nextRequest) {
      nextRequest();
    }
  }
}

// 优化的网络请求函数
export async function optimizedFetch<T>(
  endpoint: string,
  options: {
    method?: string;
    body?: any;
    params?: any;
    cacheKey?: string;
    cacheTtl?: number;
    skipCache?: boolean;
  } = {},
): Promise<T> {
  const { method = 'GET', body, params, skipCache = false } = options;
  const requestKey = options.cacheKey || generateRequestKey(endpoint, method, params || body);

  // 检查是否有相同请求正在进行
  if (!skipCache && requestCache.has(requestKey)) {
    return requestCache.get(requestKey) as Promise<T>;
  }

  // 创建请求函数
  const requestFn = async (): Promise<T> => {
    activeRequests.add(requestKey);

    try {
      // 构建请求参数
      const requestParams: any = {
        method,
      };

      if (body) {
        requestParams.body = body;
      }

      // 执行请求
      let response;
      switch (method) {
        case 'GET':
          response = await apiClient.get<T>(endpoint);
          break;
        case 'POST':
          response = await apiClient.post<T>(endpoint, requestParams.body);
          break;
        case 'DELETE':
          response = await apiClient.delete<T>(endpoint);
          break;
        default:

          /*
           * 对于其他方法，我们需要使用一个通用的方法
           * 这里我们可以使用post方法作为默认，因为它接受body参数
           */
          response = await apiClient.post<T>(endpoint, requestParams.body);
          break;
      }

      if (!response.success) {
        throw new Error(response.error || 'Request failed');
      }

      return response.data as T;
    } finally {
      activeRequests.delete(requestKey);
      requestCache.delete(requestKey);
      processRequestQueue();
    }
  };

  // 创建请求Promise
  const requestPromise = requestFn();

  // 缓存请求Promise
  if (!skipCache) {
    requestCache.set(requestKey, requestPromise);
  }

  // 检查并发限制
  if (activeRequests.size >= concurrencyLimit) {
    // 加入队列
    return new Promise<T>((resolve, reject) => {
      requestQueue.push(async () => {
        try {
          const result = await requestPromise;
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });
    });
  }
    // 立即执行
    return requestPromise;
}

// 批量请求处理
export async function batchFetch<T>(requests: Array<{
  endpoint: string;
  method?: string;
  body?: any;
  params?: any;
}>): Promise<T[]> {
  // 并发执行所有请求，但受限于并发限制
  const results = await Promise.all(
    requests.map(async req =>
      optimizedFetch<T>(req.endpoint, {
        method: req.method,
        body: req.body,
        params: req.params,
      }),
    ),
  );

  return results;
}

// 取消请求（如果支持）
export function cancelRequest(requestKey: string) {
  requestCache.delete(requestKey);
  // 从队列中移除
  const queueIndex = requestQueue.findIndex(fn =>
    // 这里简化处理，实际需要更精确的匹配
     true,
  );
  if (queueIndex > -1) {
    requestQueue.splice(queueIndex, 1);
  }
}

// 清除所有请求缓存
export function clearRequestCache() {
  requestCache.clear();
  requestQueue.length = 0;
  activeRequests.clear();
}

// 网络状态监控
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = React.useState(navigator.onLine);

  React.useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}
