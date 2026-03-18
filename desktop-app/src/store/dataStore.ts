import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// 数据状态类型
export interface DataState {
  // 分析数据
  analysisData: {
    sales: number;
    customers: number;
    conversionRate: number;
    averageOrder: number;
  };
  
  // 预测模型
  predictionModels: {
    id: string;
    name: string;
    accuracy: number;
    description: string;
  }[];
  
  // 决策建议
  decisions: {
    id: number;
    title: string;
    priority: 'high' | 'medium' | 'low';
    impact: string;
    description: string;
    status: 'recommended' | 'implemented' | 'dismissed';
  }[];
  
  // 数据加载状态
  dataLoading: {
    analysis: boolean;
    models: boolean;
    decisions: boolean;
  };
  
  // 数据错误
  dataError: string | null;
}

// 数据操作类型
export interface DataActions {
  // 数据加载
  loadAnalysisData: () => Promise<void>;
  loadPredictionModels: () => Promise<void>;
  loadDecisions: () => Promise<void>;
  
  // 数据操作
  updateDecisionStatus: (id: number, status: DataState['decisions'][0]['status']) => void;
  addDecision: (decision: Omit<DataState['decisions'][0], 'id'>) => void;
  
  // 状态更新
  setAnalysisData: (data: Partial<DataState['analysisData']>) => void;
  setPredictionModels: (models: DataState['predictionModels']) => void;
  setDecisions: (decisions: DataState['decisions']) => void;
  setDataLoading: (loading: Partial<DataState['dataLoading']>) => void;
  setDataError: (error: string | null) => void;
  
  // 重置状态
  resetDataState: () => void;
}

// 初始状态
const initialState: DataState = {
  analysisData: {
    sales: 0,
    customers: 0,
    conversionRate: 0,
    averageOrder: 0
  },
  predictionModels: [],
  decisions: [],
  dataLoading: {
    analysis: false,
    models: false,
    decisions: false
  },
  dataError: null
};

// 创建数据状态store
export const createDataStore = () => {
  return create<DataState & DataActions>()(
    persist(
      (set, get) => ({
        ...initialState,
        
        // 加载分析数据
        loadAnalysisData: async () => {
          set({ dataLoading: { ...get().dataLoading, analysis: true }, dataError: null });
          try {
            // 模拟数据加载
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // 模拟分析数据
            const analysisData = {
              sales: 120000,
              customers: 3500,
              conversionRate: 24.8,
              averageOrder: 345
            };
            
            set({ analysisData, dataLoading: { ...get().dataLoading, analysis: false } });
          } catch (error) {
            set({ dataError: '加载分析数据失败', dataLoading: { ...get().dataLoading, analysis: false } });
            throw error;
          }
        },
        
        // 加载预测模型
        loadPredictionModels: async () => {
          set({ dataLoading: { ...get().dataLoading, models: true }, dataError: null });
          try {
            // 模拟数据加载
            await new Promise(resolve => setTimeout(resolve, 1200));
            
            // 模拟模型数据
            const models = [
              { id: 'sales', name: '销售预测', accuracy: 92.5, description: '预测未来销售趋势' },
              { id: 'customer', name: '客户流失', accuracy: 87.3, description: '预测客户流失风险' },
              { id: 'inventory', name: '库存优化', accuracy: 89.7, description: '优化库存水平' },
              { id: 'price', name: '价格优化', accuracy: 90.1, description: '优化产品定价策略' },
            ];
            
            set({ predictionModels: models, dataLoading: { ...get().dataLoading, models: false } });
          } catch (error) {
            set({ dataError: '加载预测模型失败', dataLoading: { ...get().dataLoading, models: false } });
            throw error;
          }
        },
        
        // 加载决策建议
        loadDecisions: async () => {
          set({ dataLoading: { ...get().dataLoading, decisions: true }, dataError: null });
          try {
            // 模拟数据加载
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // 模拟决策数据
            const decisions: { id: number; title: string; priority: 'high' | 'medium' | 'low'; impact: string; description: string; status: 'recommended' | 'implemented' | 'dismissed' }[] = [
              {
                id: 1,
                title: '优化供应链管理',
                priority: 'high',
                impact: '运营成本降低15%',
                description: '通过数据分析优化供应链流程，减少库存积压',
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
            ];
            
            set({ decisions, dataLoading: { ...get().dataLoading, decisions: false } });
          } catch (error) {
            set({ dataError: '加载决策建议失败', dataLoading: { ...get().dataLoading, decisions: false } });
            throw error;
          }
        },
        
        // 更新决策状态
        updateDecisionStatus: (id, status) => {
          set(state => ({
            decisions: state.decisions.map(decision => 
              decision.id === id ? { ...decision, status } : decision
            )
          }));
        },
        
        // 添加决策
        addDecision: (decision) => {
          set(state => ({
            decisions: [...state.decisions, {
              ...decision,
              id: Math.max(0, ...state.decisions.map(d => d.id)) + 1
            }]
          }));
        },
        
        // 状态更新
        setAnalysisData: (data) => set(state => ({
          analysisData: { ...state.analysisData, ...data }
        })),
        setPredictionModels: (models) => set({ predictionModels: models }),
        setDecisions: (decisions) => set({ decisions }),
        setDataLoading: (loading) => set(state => ({
          dataLoading: { ...state.dataLoading, ...loading }
        })),
        setDataError: (error) => set({ dataError: error }),
        
        // 重置状态
        resetDataState: () => set(initialState)
      }),
      {
        name: 'data-storage',
        partialize: (state) => ({
          analysisData: state.analysisData,
          predictionModels: state.predictionModels,
          decisions: state.decisions
        })
      }
    )
  );
};
