import React, { useState, useEffect } from 'react';
import { OptimizedMotion, getOptimizedAnimation } from '../utils/animationUtils';
import { Link } from 'react-router-dom';

const motion = OptimizedMotion;

function Home() {
  const [isElectron, setIsElectron] = useState(false);

  useEffect(() => {
    // 检测是否在Electron环境中运行
    setIsElectron(!!(window.process && window.process.type === 'renderer'));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white p-8">
      <motion.div
        {...getOptimizedAnimation('fadeInUp')}
        className="max-w-4xl mx-auto"
      >
        <header className="mb-12">
          <motion.h1 
            className="text-4xl font-bold mb-4"
            {...getOptimizedAnimation('scaleIn')}
          >
            AI决策系统
          </motion.h1>
          <p className="text-xl text-blue-200">
            智能辅助决策，提升业务效率
          </p>
          {isElectron && (
            <div className="mt-4 bg-blue-800/30 rounded-lg p-3 inline-block">
              <span className="text-sm">运行在 Electron 环境中</span>
            </div>
          )}
        </header>

        <main className="space-y-8">
          <motion.section 
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6"
            {...getOptimizedAnimation('cardHover')}
          >
            <h2 className="text-2xl font-semibold mb-4">欢迎使用</h2>
            <p className="mb-6">
              这是一个基于 Electron 和 React 构建的桌面应用，集成了 AI 决策系统的核心功能。
            </p>
          </motion.section>

          <motion.section 
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6"
            {...getOptimizedAnimation('cardHover')}
          >
            <h2 className="text-2xl font-semibold mb-4">功能模块</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { name: '数据分析', description: '智能分析业务数据', path: '/data-analysis' },
                { name: '预测模型', description: '基于AI的预测分析', path: '/prediction-model' },
                { name: '决策建议', description: '智能生成决策方案', path: '/decision-suggestion' },
                { name: '系统设置', description: '应用配置和管理', path: '/system-settings' }
              ].map((module, index) => (
                <motion.div 
                  key={index}
                  {...getOptimizedAnimation('hoverEffect')}
                >
                  <Link to={module.path} className="block bg-white/5 rounded-lg p-4 border border-white/10 hover:border-blue-400 transition-colors">
                    <h3 className="font-semibold mb-2">{module.name}</h3>
                    <p className="text-sm text-blue-200">{module.description}</p>
                  </Link>
                </motion.div>
              ))}
            </div>
          </motion.section>
        </main>

        <footer className="mt-16 text-center text-sm text-blue-200">
          <p>AI决策系统 © {new Date().getFullYear()}</p>
          <p className="mt-2">版本 1.0.0</p>
        </footer>
      </motion.div>
    </div>
  );
}

export default React.memo(Home);