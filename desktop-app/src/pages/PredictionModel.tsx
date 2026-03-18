import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

function PredictionModel() {
  const [loading, setLoading] = useState(true);
  const [models, setModels] = useState<any[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('sales');

  useEffect(() => {
    // 模拟模型加载
    const loadModels = async () => {
      setLoading(true);
      try {
        // 模拟网络请求延迟
        await new Promise(resolve => setTimeout(resolve, 1200));
        // 模拟模型数据
        setModels([
          { id: 'sales', name: '销售预测', accuracy: 92.5, description: '预测未来销售趋势' },
          { id: 'customer', name: '客户流失', accuracy: 87.3, description: '预测客户流失风险' },
          { id: 'inventory', name: '库存优化', accuracy: 89.7, description: '优化库存水平' },
          { id: 'price', name: '价格优化', accuracy: 90.1, description: '优化产品定价策略' },
        ]);
      } catch (error) {
        console.error('加载模型失败:', error);
      } finally {
        setLoading(false);
      }
    };

    loadModels();
  }, []);

  // 使用useMemo优化模型选择
  const currentModel = useMemo(() => {
    return models.find(model => model.id === selectedModel) || models[0];
  }, [models, selectedModel]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white p-8 flex items-center justify-center">
        <div className="text-2xl">加载预测模型中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold">预测模型</h1>
            <Link to="/" className="bg-blue-700 hover:bg-blue-600 px-4 py-2 rounded-lg transition-colors">
              返回首页
            </Link>
          </div>
          <p className="text-blue-200 mt-2">基于AI的预测分析，辅助业务决策</p>
        </header>

        <main className="space-y-8">
          <motion.section 
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-2xl font-semibold mb-6">模型选择</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {models.map((model) => (
                <motion.div 
                  key={model.id}
                  className={`rounded-lg p-4 border cursor-pointer transition-colors ${selectedModel === model.id ? 'bg-blue-800/50 border-blue-400' : 'bg-white/5 border-white/10 hover:bg-white/10'}`}
                  whileHover={{ y: -2 }}
                  transition={{ duration: 0.2 }}
                  onClick={() => setSelectedModel(model.id)}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">{model.name}</h3>
                    <span className="bg-green-800/50 text-green-300 text-sm px-2 py-1 rounded">
                      {model.accuracy}% 准确率
                    </span>
                  </div>
                  <p className="text-sm text-blue-200 mt-2">{model.description}</p>
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
            <h2 className="text-2xl font-semibold mb-4">{currentModel?.name}预测</h2>
            <div className="space-y-4">
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <h3 className="font-medium mb-3">预测参数</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm mb-1">预测周期</label>
                    <select className="w-full bg-white/10 border border-white/20 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-400">
                      <option>1个月</option>
                      <option>3个月</option>
                      <option>6个月</option>
                      <option>12个月</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm mb-1">预测精度</label>
                    <select className="w-full bg-white/10 border border-white/20 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-400">
                      <option>标准</option>
                      <option>高精度</option>
                      <option>快速</option>
                    </select>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end">
                <motion.button 
                  className="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-lg transition-colors font-medium"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                >
                  开始预测
                </motion.button>
              </div>
            </div>
          </motion.section>
        </main>
      </div>
    </div>
  );
}

export default React.memo(PredictionModel);