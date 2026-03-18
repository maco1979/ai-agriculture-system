import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useMemoryMonitor } from '../hooks/useMemoryMonitor';

function SystemSettings() {
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState<any>({
    notifications: true,
    autoUpdate: false,
    theme: 'dark',
    language: 'zh-CN',
    cacheSize: '512MB'
  });
  const [systemInfo, setSystemInfo] = useState<any>({});
  const { memoryData } = useMemoryMonitor();

  useEffect(() => {
    // 模拟设置加载
    const loadSettings = async () => {
      setLoading(true);
      try {
        // 模拟网络请求延迟
        await new Promise(resolve => setTimeout(resolve, 900));
        // 模拟系统信息
        setSystemInfo({
          version: '1.0.0',
          electronVersion: '39.2.7',
          nodeVersion: '20.10.0',
          platform: 'win32',
          arch: 'x64',
          memory: '8GB',
          cpu: 'Intel Core i7'
        });
      } catch (error) {
        console.error('加载设置失败:', error);
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  // 处理设置变更
  const handleSettingChange = (key: string, value: any) => {
    setSettings((prev: any) => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white p-8 flex items-center justify-center">
        <div className="text-2xl">加载系统设置中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold">系统设置</h1>
            <Link to="/" className="bg-blue-700 hover:bg-blue-600 px-4 py-2 rounded-lg transition-colors">
              返回首页
            </Link>
          </div>
          <p className="text-blue-200 mt-2">应用配置和管理</p>
        </header>

        <main className="space-y-8">
          <motion.section 
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-2xl font-semibold mb-6">基本设置</h2>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">通知提醒</h3>
                  <p className="text-sm text-blue-200">接收系统通知</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    className="sr-only peer"
                    checked={settings.notifications}
                    onChange={(e) => handleSettingChange('notifications', e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">自动更新</h3>
                  <p className="text-sm text-blue-200">自动检查并安装更新</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    className="sr-only peer"
                    checked={settings.autoUpdate}
                    onChange={(e) => handleSettingChange('autoUpdate', e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">主题</h3>
                  <p className="text-sm text-blue-200">应用显示主题</p>
                </div>
                <select 
                  className="bg-white/10 border border-white/20 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-400"
                  value={settings.theme}
                  onChange={(e) => handleSettingChange('theme', e.target.value)}
                >
                  <option value="dark">深色</option>
                  <option value="light">浅色</option>
                </select>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">语言</h3>
                  <p className="text-sm text-blue-200">应用界面语言</p>
                </div>
                <select 
                  className="bg-white/10 border border-white/20 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-400"
                  value={settings.language}
                  onChange={(e) => handleSettingChange('language', e.target.value)}
                >
                  <option value="zh-CN">简体中文</option>
                  <option value="en-US">English</option>
                </select>
              </div>
            </div>
          </motion.section>

          <motion.section 
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <h2 className="text-2xl font-semibold mb-6">系统信息</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(systemInfo).map(([key, value]) => (
                <div key={key} className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <h3 className="text-sm text-blue-300 mb-1">{key === 'version' ? '应用版本' : key === 'electronVersion' ? 'Electron版本' : key === 'nodeVersion' ? 'Node.js版本' : key === 'platform' ? '平台' : key === 'arch' ? '架构' : key === 'memory' ? '内存' : key === 'cpu' ? 'CPU' : key}</h3>
                  <p className="font-medium">{String(value)}</p>
                </div>
              ))}
            </div>
          </motion.section>

          <motion.section 
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <h2 className="text-2xl font-semibold mb-6">内存监控</h2>
            {memoryData ? (
              <div className="space-y-6">
                <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <h3 className="text-lg font-medium mb-4">系统内存</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>总内存:</span>
                      <span className="font-medium">{memoryData.system.total}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>已用内存:</span>
                      <span className="font-medium">{memoryData.system.used} ({memoryData.system.usedPercent}%)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>可用内存:</span>
                      <span className="font-medium">{memoryData.system.free}</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2.5 mt-2">
                      <div 
                        className="bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${memoryData.system.usedPercent}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <h3 className="text-lg font-medium mb-4">进程内存</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>物理内存 (RSS):</span>
                      <span className="font-medium">{memoryData.process.rss}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>堆内存总量:</span>
                      <span className="font-medium">{memoryData.process.heapTotal}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>已用堆内存:</span>
                      <span className="font-medium">{memoryData.process.heapUsed}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>外部内存:</span>
                      <span className="font-medium">{memoryData.process.external}</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-10">
                <p>加载内存信息中...</p>
              </div>
            )}
          </motion.section>

          <motion.section 
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <h2 className="text-2xl font-semibold mb-6">高级设置</h2>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">缓存大小</h3>
                  <p className="text-sm text-blue-200">应用缓存容量</p>
                </div>
                <select 
                  className="bg-white/10 border border-white/20 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-400"
                  value={settings.cacheSize}
                  onChange={(e) => handleSettingChange('cacheSize', e.target.value)}
                >
                  <option value="256MB">256MB</option>
                  <option value="512MB">512MB</option>
                  <option value="1GB">1GB</option>
                </select>
              </div>

              <div className="flex justify-end space-x-4">
                <button className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition-colors">
                  恢复默认
                </button>
                <button className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-lg transition-colors">
                  保存设置
                </button>
              </div>
            </div>
          </motion.section>
        </main>
      </div>
    </div>
  );
}

export default React.memo(SystemSettings);