import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

function DataAnalysis() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    // 模拟数据加载
    const loadData = async () => {
      setLoading(true);
      try {
        // 模拟网络请求延迟
        await new Promise(resolve => setTimeout(resolve, 1000));
        // 模拟数据
        setData([
          { id: 1, name: '销售数据', value: 120000, trend: 5.2 },
          { id: 2, name: '客户数量', value: 3500, trend: 12.5 },
          { id: 3, name: '转化率', value: 24.8, trend: -2.1 },
          { id: 4, name: '平均订单', value: 345, trend: 8.7 },
        ]);
      } catch (error) {
        console.error('加载数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // 使用useMemo优化数据计算
  const formattedData = useMemo(() => {
    return data.map(item => ({
      ...item,
      trendClass: item.trend >= 0 ? 'text-green-400' : 'text-red-400',
      trendIcon: item.trend >= 0 ? '↑' : '↓',
    }));
  }, [data]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white p-8 flex items-center justify-center">
        <div className="text-2xl">加载数据分析中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold">数据分析</h1>
            <Link to="/" className="bg-blue-700 hover:bg-blue-600 px-4 py-2 rounded-lg transition-colors">
              返回首页
            </Link>
          </div>
          <p className="text-blue-200 mt-2">智能分析业务数据，提供数据洞察</p>
        </header>

        <main className="space-y-8">
          <motion.section 
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-2xl font-semibold mb-6">关键指标</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {formattedData.map((item) => (
                <motion.div 
                  key={item.id}
                  className="bg-white/5 rounded-lg p-4 border border-white/10"
                  whileHover={{ y: -3, backgroundColor: 'rgba(255,255,255,0.1)' }}
                  transition={{ duration: 0.2 }}
                >
                  <h3 className="font-medium mb-2">{item.name}</h3>
                  <div className="flex items-end justify-between">
                    <span className="text-2xl font-bold">{item.value}</span>
                    <span className={`${item.trendClass} flex items-center gap-1`}>
                      {item.trendIcon} {Math.abs(item.trend)}%
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.section>

          <motion.section 
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <h2 className="text-2xl font-semibold mb-4">分析工具</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { name: '趋势分析', description: '分析数据趋势变化' },
                { name: '对比分析', description: '比较不同时期数据' },
                { name: '预测分析', description: '基于历史数据预测' },
              ].map((tool, index) => (
                <motion.div 
                  key={index}
                  className="bg-white/5 rounded-lg p-4 border border-white/10"
                  whileHover={{ scale: 1.02 }}
                  transition={{ duration: 0.2 }}
                >
                  <h3 className="font-semibold mb-2">{tool.name}</h3>
                  <p className="text-sm text-blue-200">{tool.description}</p>
                  <button className="mt-4 bg-blue-700/50 hover:bg-blue-700 px-3 py-1 rounded text-sm transition-colors">
                    使用工具
                  </button>
                </motion.div>
              ))}
            </div>
          </motion.section>
        </main>
      </div>
    </div>
  );
}

export default React.memo(DataAnalysis);