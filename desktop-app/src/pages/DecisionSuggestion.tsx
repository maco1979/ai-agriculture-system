import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

function DecisionSuggestion() {
  const [loading, setLoading] = useState(true);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [priority, setPriority] = useState<string>('high');

  useEffect(() => {
    // 模拟建议加载
    const loadSuggestions = async () => {
      setLoading(true);
      try {
        // 模拟网络请求延迟
        await new Promise(resolve => setTimeout(resolve, 1000));
        // 模拟建议数据
        setSuggestions([
          {
            id: 1,
            title: '优化库存管理',
            priority: 'high',
            impact: '销售效率提升15%',
            description: '基于历史销售数据，优化库存水平，减少滞销品',
            status: 'recommended'
          },
          {
            id: 2,
            title: '调整定价策略',
            priority: 'medium',
            impact: '利润率提升8%',
            description: '根据市场竞争情况，调整产品定价策略',
            status: 'recommended'
          },
          {
            id: 3,
            title: '增加营销投入',
            priority: 'medium',
            impact: '客户获取成本降低12%',
            description: '优化营销渠道，增加高转化渠道的投入',
            status: 'recommended'
          },
          {
            id: 4,
            title: '改进客户服务',
            priority: 'low',
            impact: '客户满意度提升20%',
            description: '优化客户服务流程，提高响应速度',
            status: 'recommended'
          },
        ]);
      } catch (error) {
        console.error('加载建议失败:', error);
      } finally {
        setLoading(false);
      }
    };

    loadSuggestions();
  }, []);

  // 使用useMemo优化建议过滤
  const filteredSuggestions = useMemo(() => {
    if (priority === 'all') {
      return suggestions;
    }
    return suggestions.filter(suggestion => suggestion.priority === priority);
  }, [suggestions, priority]);

  const getPriorityClass = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-800/50 text-red-300';
      case 'medium': return 'bg-yellow-800/50 text-yellow-300';
      case 'low': return 'bg-green-800/50 text-green-300';
      default: return 'bg-gray-800/50 text-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white p-8 flex items-center justify-center">
        <div className="text-2xl">加载决策建议中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold">决策建议</h1>
            <Link to="/" className="bg-blue-700 hover:bg-blue-600 px-4 py-2 rounded-lg transition-colors">
              返回首页
            </Link>
          </div>
          <p className="text-blue-200 mt-2">智能生成决策方案，提升业务表现</p>
        </header>

        <main className="space-y-8">
          <motion.section 
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold">建议列表</h2>
              <div className="flex gap-2">
                {['all', 'high', 'medium', 'low'].map((level) => (
                  <button
                    key={level}
                    className={`px-3 py-1 rounded-full text-sm transition-colors ${priority === level ? 'bg-blue-600' : 'bg-white/10 hover:bg-white/20'}`}
                    onClick={() => setPriority(level)}
                  >
                    {level === 'all' ? '全部' : level === 'high' ? '高优先级' : level === 'medium' ? '中优先级' : '低优先级'}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="space-y-4">
              {filteredSuggestions.map((suggestion) => (
                <motion.div 
                  key={suggestion.id}
                  className="bg-white/5 backdrop-blur-sm rounded-lg p-5 border border-white/10"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  whileHover={{ scale: 1.01, backgroundColor: 'rgba(255,255,255,0.1)' }}
                >
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-xl font-semibold">{suggestion.title}</h3>
                    <span className={`${getPriorityClass(suggestion.priority)} text-xs px-2 py-1 rounded-full`}>
                      {suggestion.priority === 'high' ? '高' : suggestion.priority === 'medium' ? '中' : '低'}优先级
                    </span>
                  </div>
                  <p className="text-blue-200 mb-3">{suggestion.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="bg-green-800/50 text-green-300 text-sm px-3 py-1 rounded">
                      {suggestion.impact}
                    </span>
                    <button className="bg-blue-700 hover:bg-blue-600 px-4 py-1 rounded text-sm transition-colors">
                      应用建议
                    </button>
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
            <h2 className="text-2xl font-semibold mb-4">建议生成器</h2>
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <h3 className="font-medium mb-3">输入业务场景</h3>
              <textarea 
                className="w-full bg-white/10 border border-white/20 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-400 h-32"
                placeholder="描述您的业务场景，例如：如何提高产品销量，如何降低运营成本等..."
              ></textarea>
              <div className="mt-4 flex justify-end">
                <motion.button 
                  className="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-lg transition-colors font-medium"
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  transition={{ duration: 0.2 }}
                >
                  生成建议
                </motion.button>
              </div>
            </div>
          </motion.section>
        </main>
      </div>
    </div>
  );
}

export default React.memo(DecisionSuggestion);