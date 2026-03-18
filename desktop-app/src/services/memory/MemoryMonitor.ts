import os from 'os';

// 扩展全局类型
declare global {
  var mainWindow: any;
}

class MemoryMonitor {
  private intervalId: NodeJS.Timeout | null = null;
  private threshold: number = 80; // 内存使用率阈值（百分比）

  startMonitoring(interval: number = 5000) {
    this.stopMonitoring();
    
    this.intervalId = setInterval(() => {
      const memoryInfo = this.getMemoryInfo();
      const memoryUsagePercent = memoryInfo.usedPercent;
      
      if (memoryUsagePercent > this.threshold) {
        this.handleHighMemoryUsage(memoryInfo);
      }

      // 发送内存使用信息到渲染进程
      if (global.mainWindow) {
        global.mainWindow.webContents.send('memory-usage', memoryInfo);
      }
    }, interval);
  }

  stopMonitoring() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  getMemoryInfo() {
    const totalMemory = os.totalmem();
    const freeMemory = os.freemem();
    const usedMemory = totalMemory - freeMemory;
    const usedPercent = Math.round((usedMemory / totalMemory) * 100);

    return {
      total: this.formatBytes(totalMemory),
      free: this.formatBytes(freeMemory),
      used: this.formatBytes(usedMemory),
      usedPercent,
      totalBytes: totalMemory,
      freeBytes: freeMemory,
      usedBytes: usedMemory
    };
  }

  private handleHighMemoryUsage(memoryInfo: any) {
    console.warn(`High memory usage detected: ${memoryInfo.usedPercent}%`);
    // 这里可以实现内存释放策略
    this.optimizeMemoryUsage();
  }

  private optimizeMemoryUsage() {
    // 实现内存优化策略
    console.log('Optimizing memory usage...');
    // 1. 清理缓存
    // 2. 释放不再使用的资源
    // 3. 调整应用行为
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  setThreshold(threshold: number) {
    this.threshold = threshold;
  }

  getProcessMemoryInfo() {
    const processMemory = process.memoryUsage();
    return {
      rss: this.formatBytes(processMemory.rss),
      heapTotal: this.formatBytes(processMemory.heapTotal),
      heapUsed: this.formatBytes(processMemory.heapUsed),
      external: this.formatBytes(processMemory.external),
      rssBytes: processMemory.rss,
      heapTotalBytes: processMemory.heapTotal,
      heapUsedBytes: processMemory.heapUsed,
      externalBytes: processMemory.external
    };
  }
}

export const memoryMonitor = new MemoryMonitor();
