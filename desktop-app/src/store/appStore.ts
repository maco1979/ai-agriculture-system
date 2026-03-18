import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// 应用状态类型
export interface AppState {
  // 应用状态
  isLoading: boolean;
  isElectron: boolean;
  appVersion: string;
  
  // UI状态
  sidebarOpen: boolean;
  activePage: string;
  
  // 性能状态
  performance: {
    startupTime: number;
    lastRenderTime: number;
  };
}

// 应用操作类型
export interface AppActions {
  // 状态更新
  setLoading: (loading: boolean) => void;
  setIsElectron: (isElectron: boolean) => void;
  setAppVersion: (version: string) => void;
  
  // UI操作
  toggleSidebar: () => void;
  setActivePage: (page: string) => void;
  
  // 性能监控
  updatePerformance: (performance: Partial<AppState['performance']>) => void;
  
  // 重置状态
  resetAppState: () => void;
}

// 初始状态
const initialState: AppState = {
  isLoading: false,
  isElectron: false,
  appVersion: '1.0.0',
  sidebarOpen: true,
  activePage: '/',
  performance: {
    startupTime: 0,
    lastRenderTime: 0
  }
};

// 创建应用状态store
export const createAppStore = () => {
  return create<AppState & AppActions>()(
    persist(
      (set) => ({
        ...initialState,
        
        // 状态更新
        setLoading: (loading) => set({ isLoading: loading }),
        setIsElectron: (isElectron) => set({ isElectron }),
        setAppVersion: (version) => set({ appVersion: version }),
        
        // UI操作
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
        setActivePage: (page) => set({ activePage: page }),
        
        // 性能监控
        updatePerformance: (performance) => set((state) => ({
          performance: { ...state.performance, ...performance }
        })),
        
        // 重置状态
        resetAppState: () => set(initialState)
      }),
      {
        name: 'app-storage',
        partialize: (state) => ({
          sidebarOpen: state.sidebarOpen,
          activePage: state.activePage,
          appVersion: state.appVersion
        })
      }
    )
  );
};
