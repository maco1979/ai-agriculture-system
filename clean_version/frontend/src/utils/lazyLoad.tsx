import type { ComponentType } from 'react';
import React, { lazy, Suspense } from 'react';

interface LazyLoadOptions {
  fallback?: React.ReactNode;
  preload?: boolean;
}

interface LazyComponent<T extends ComponentType<any>> {
  default: React.LazyExoticComponent<T>;
  preload: () => Promise<void>;
}

/**
 * 增强的懒加载函数，支持组件预加载
 * @param importFn 动态导入函数
 * @param options 配置选项
 * @returns 懒加载组件和预加载函数
 */
export function lazyWithPreload<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {},
): LazyComponent<T> {
  const Component = lazy(importFn);

  let promise: Promise<void> | null = null;

  const preload = async (): Promise<void> => {
    if (!promise) {
      promise = importFn().then(() => {});
    }
    return promise;
  };

  // 如果设置了预加载，则立即执行
  if (options.preload) {
    preload();
  }

  return {
    default: Component,
    preload,
  };
}

/**
 * 懒加载组件包装器，提供统一的fallback
 * @param Component 懒加载组件
 * @param fallback 加载中的占位符
 * @returns 包装后的组件
 */
export function withLazyFallback<T extends ComponentType<any>>(
  Component: T,
  fallback?: React.ReactNode,
): ComponentType<T> {
  const defaultFallback = <div className="flex h-screen items-center justify-center text-white">加载中...</div>;
  const finalFallback = fallback || defaultFallback;

  return (props: any) => (
    <Suspense fallback={finalFallback}>
      <Component {...props} />
    </Suspense>
  );
}

/**
 * 路由级别的代码分割配置
 */
export const routeConfig = {
  dashboard: {
    component: lazyWithPreload(async () => import('@/pages/Dashboard').then(module => ({ default: module.Dashboard }))),
    path: '/',
    preload: true,
  },
  agriculture: {
    component: lazyWithPreload(async () => import('@/pages/Agriculture')),
    path: '/agriculture',
  },
  models: {
    component: lazyWithPreload(async () => import('@/pages/ModelManagement').then(module => ({ default: module.ModelManagement }))),
    path: '/models',
  },
  modelDetail: {
    component: lazyWithPreload(async () => import('@/pages/ModelDetail').then(module => ({ default: module.ModelDetail }))),
    path: '/models/:id',
  },
  inference: {
    component: lazyWithPreload(async () => import('@/pages/InferenceService').then(module => ({ default: module.InferenceService }))),
    path: '/inference',
  },
  blockchain: {
    component: lazyWithPreload(async () => import('@/pages/Blockchain').then(module => ({ default: module.Blockchain }))),
    path: '/blockchain',
  },
  federated: {
    component: lazyWithPreload(async () => import('@/pages/FederatedLearning').then(module => ({ default: module.FederatedLearning }))),
    path: '/federated',
  },
  monitoring: {
    component: lazyWithPreload(async () => import('@/pages/MonitoringDashboard').then(module => ({ default: module.MonitoringDashboard }))),
    path: '/monitoring',
  },
  performance: {
    component: lazyWithPreload(async () => import('@/pages/PerformanceMonitoring').then(module => ({ default: module.PerformanceMonitoring }))),
    path: '/performance',
  },
  settings: {
    component: lazyWithPreload(async () => import('@/pages/Settings').then(module => ({ default: module.Settings }))),
    path: '/settings',
  },
  community: {
    component: lazyWithPreload(async () => import('@/pages/Community')),
    path: '/community',
  },
  aiControl: {
    component: lazyWithPreload(async () => import('@/pages/AIControl').then(module => ({ default: module.AIControl }))),
    path: '/ai-control',
  },
  login: {
    component: lazyWithPreload(async () => import('@/pages/Login')),
    path: '/login',
  },
};

/**
 * 预加载指定路由的组件
 * @param routeNames 路由名称数组
 */
export async function preloadRoutes(routeNames: Array<keyof typeof routeConfig>): Promise<void[]> {
  return Promise.all(
    routeNames.map(async routeName => {
      const route = routeConfig[routeName];
      return route.component.preload() || Promise.resolve();
    }),
  );
}

/**
 * 预加载用户可能接下来访问的路由
 * 基于当前路由和用户行为模式
 */
export function preloadRelatedRoutes(currentRoute: string): void {
  const routeMap: Record<string, Array<keyof typeof routeConfig>> = {
    '/': ['models', 'inference', 'dashboard'],
    '/models': ['modelDetail', 'inference'],
    '/models/:id': ['models', 'inference'],
    '/inference': ['models', 'performance'],
    '/agriculture': ['dashboard', 'inference'],
    '/blockchain': ['federated'],
    '/federated': ['blockchain'],
    '/monitoring': ['performance', 'settings'],
    '/performance': ['monitoring', 'settings'],
    '/settings': ['dashboard'],
    '/community': ['dashboard'],
    '/ai-control': ['dashboard', 'monitoring'],
  };

  const relatedRoutes = routeMap[currentRoute] || [];
  if (relatedRoutes.length > 0) {
    preloadRoutes(relatedRoutes).catch(err => {
      console.warn('预加载路由失败:', err);
    });
  }
}
