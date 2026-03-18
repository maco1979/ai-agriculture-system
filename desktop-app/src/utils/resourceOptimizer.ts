// 资源加载优化工具
import { useState } from 'react';

// 资源缓存管理
class ResourceCache {
  private cache: Map<string, { data: any; timestamp: number; ttl: number }> = new Map();
  private maxSize: number = 100;

  // 获取缓存资源
  get(key: string) {
    const item = this.cache.get(key);
    if (!item) return null;

    // 检查缓存是否过期
    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  // 设置缓存资源
  set(key: string, data: any, ttl: number = 3600000) { // 默认1小时
    // 限制缓存大小
    if (this.cache.size >= this.maxSize) {
      this.evictOldest();
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  // 删除缓存资源
  delete(key: string) {
    this.cache.delete(key);
  }

  // 清空缓存
  clear() {
    this.cache.clear();
  }

  // 驱逐最旧的缓存项
  private evictOldest() {
    let oldestKey: string | null = null;
    let oldestTimestamp: number = Infinity;

    for (const [key, item] of this.cache.entries()) {
      if (item.timestamp < oldestTimestamp) {
        oldestTimestamp = item.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }

  // 获取缓存大小
  getSize() {
    return this.cache.size;
  }
}

// 全局资源缓存实例
export const resourceCache = new ResourceCache();

// 图片懒加载
export const lazyLoadImage = (img: HTMLImageElement, src: string) => {
  if (!img) return;

  // 检查是否已加载
  if (img.dataset.loaded === 'true') return;

  // 创建图片对象
  const image = new Image();
  image.src = src;

  image.onload = () => {
    img.src = src;
    img.dataset.loaded = 'true';
    img.classList.add('loaded');
  };

  image.onerror = () => {
    img.dataset.loaded = 'error';
    img.classList.add('error');
  };
};

// 批量资源预加载
export const preloadResources = async (resources: Array<{ type: string; url: string }>) => {
  const promises = resources.map(resource => {
    return new Promise<void>((resolve) => {
      if (resource.type === 'image') {
        const img = new Image();
        img.src = resource.url;
        img.onload = img.onerror = () => resolve();
      } else if (resource.type === 'script') {
        const script = document.createElement('script');
        script.src = resource.url;
        script.onload = script.onerror = () => resolve();
        document.head.appendChild(script);
      } else if (resource.type === 'style') {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = resource.url;
        link.onload = link.onerror = () => resolve();
        document.head.appendChild(link);
      } else {
        resolve();
      }
    });
  });

  await Promise.all(promises);
};

// 资源加载性能监控
export const trackResourceLoad = (resourceName: string) => {
  const startTime = performance.now();
  return () => {
    const endTime = performance.now();
    console.log(`${resourceName} 资源加载时间: ${(endTime - startTime).toFixed(2)}ms`);
  };
};

// 条件加载资源（根据网络状况）
export const conditionalLoadResource = (_url: string, options: { lowBandwidth?: boolean; critical?: boolean } = {}) => {
  const { lowBandwidth = false, critical = false } = options;

  // 检查网络状况
  const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
  const isSlowConnection = connection && (connection.effectiveType === '2g' || connection.downlink < 1);

  // 如果是关键资源或网络状况良好，则加载
  if (critical || !isSlowConnection && !lowBandwidth) {
    return true;
  }

  return false;
};

// 资源优先级管理
export class ResourcePrioritizer {
  private highPriority: Array<{ url: string; type: string }> = [];
  private mediumPriority: Array<{ url: string; type: string }> = [];
  private lowPriority: Array<{ url: string; type: string }> = [];

  // 添加资源到优先级队列
  addResource(url: string, type: string, priority: 'high' | 'medium' | 'low' = 'medium') {
    if (priority === 'high') {
      this.highPriority.push({ url, type });
    } else if (priority === 'medium') {
      this.mediumPriority.push({ url, type });
    } else {
      this.lowPriority.push({ url, type });
    }
  }

  // 按优先级加载资源
  async loadResources() {
    // 先加载高优先级资源
    if (this.highPriority.length > 0) {
      await preloadResources(this.highPriority);
    }

    // 延迟加载中等优先级资源
    setTimeout(async () => {
      if (this.mediumPriority.length > 0) {
        await preloadResources(this.mediumPriority);
      }

      // 最后加载低优先级资源
      setTimeout(async () => {
        if (this.lowPriority.length > 0) {
          await preloadResources(this.lowPriority);
        }
      }, 1000);
    }, 500);
  }

  // 清空资源队列
  clear() {
    this.highPriority = [];
    this.mediumPriority = [];
    this.lowPriority = [];
  }
}

// 全局资源优先级管理器实例
export const resourcePrioritizer = new ResourcePrioritizer();

// 计算资源大小
export const calculateResourceSize = (data: any): string => {
  if (!data) return '0 B';

  let size: number;
  if (typeof data === 'string') {
    size = new Blob([data]).size;
  } else if (data instanceof Blob) {
    size = data.size;
  } else if (data instanceof ArrayBuffer) {
    size = data.byteLength;
  } else {
    size = JSON.stringify(data).length;
  }

  const units = ['B', 'KB', 'MB', 'GB'];
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(2)} ${units[unitIndex]}`;
};

// 网络请求缓存策略
export const cachedFetch = async (url: string, options: RequestInit = {}, ttl: number = 3600000) => {
  const cacheKey = `fetch_${url}_${JSON.stringify(options)}`;

  // 检查缓存
  const cachedData = resourceCache.get(cacheKey);
  if (cachedData) {
    return cachedData;
  }

  // 发起网络请求
  try {
    const response = await fetch(url, options);
    const data = await response.json();

    // 缓存响应数据
    resourceCache.set(cacheKey, data, ttl);

    return data;
  } catch (error) {
    console.error('Cached fetch error:', error);
    throw error;
  }
};

// 资源加载状态管理
export const useResourceLoader = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadResource = async (url: string, options: RequestInit = {}) => {
    setLoading(true);
    setError(null);

    try {
      const data = await cachedFetch(url, options);
      setLoading(false);
      return data;
    } catch (err) {
      setError(err as Error);
      setLoading(false);
      throw err;
    }
  };

  return { loading, error, loadResource };
};


