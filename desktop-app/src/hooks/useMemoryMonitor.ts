import { useState, useEffect, useCallback } from 'react';
import { ipcRenderer } from 'electron';

interface MemoryInfo {
  total: string;
  free: string;
  used: string;
  usedPercent: number;
  totalBytes: number;
  freeBytes: number;
  usedBytes: number;
}

interface ProcessMemoryInfo {
  rss: string;
  heapTotal: string;
  heapUsed: string;
  external: string;
  rssBytes: number;
  heapTotalBytes: number;
  heapUsedBytes: number;
  externalBytes: number;
}

interface MemoryData {
  system: MemoryInfo;
  process: ProcessMemoryInfo;
}

export const useMemoryMonitor = (interval: number = 5000) => {
  const [memoryData, setMemoryData] = useState<MemoryData | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);

  const getMemoryInfo = useCallback(() => {
    ipcRenderer.send('get-memory-info');
  }, []);

  const startMonitoring = useCallback(() => {
    ipcRenderer.send('start-memory-monitoring', interval);
    setIsMonitoring(true);
  }, [interval]);

  const stopMonitoring = useCallback(() => {
    ipcRenderer.send('stop-memory-monitoring');
    setIsMonitoring(false);
  }, []);

  useEffect(() => {
    // 监听内存使用信息
    const handleMemoryUsage = (_event: any, data: MemoryInfo) => {
      setMemoryData(prev => {
        if (prev) {
          return {
            ...prev,
            system: data
          };
        }
        return null;
      });
    };

    // 监听内存信息响应
    const handleMemoryInfo = (_event: any, data: MemoryData) => {
      setMemoryData(data);
    };

    // 注册事件监听器
    ipcRenderer.on('memory-usage', handleMemoryUsage);
    ipcRenderer.on('memory-info', handleMemoryInfo);

    // 初始获取内存信息
    getMemoryInfo();

    // 启动监控
    startMonitoring();

    // 清理函数
    return () => {
      ipcRenderer.off('memory-usage', handleMemoryUsage);
      ipcRenderer.off('memory-info', handleMemoryInfo);
      stopMonitoring();
    };
  }, [getMemoryInfo, startMonitoring, stopMonitoring]);

  return {
    memoryData,
    isMonitoring,
    getMemoryInfo,
    startMonitoring,
    stopMonitoring
  };
};
