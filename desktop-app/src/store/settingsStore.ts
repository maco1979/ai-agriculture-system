import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// 设置状态类型
export interface SettingsState {
  // 应用设置
  appSettings: {
    notifications: boolean;
    autoUpdate: boolean;
    theme: 'light' | 'dark' | 'system';
    language: string;
    cacheSize: string;
  };
  
  // 性能设置
  performanceSettings: {
    hardwareAcceleration: boolean;
    backgroundThrottling: boolean;
    gpuRasterization: boolean;
  };
  
  // 网络设置
  networkSettings: {
    timeout: number;
    retryAttempts: number;
    cacheEnabled: boolean;
  };
  
  // 设置版本
  settingsVersion: string;
}

// 设置操作类型
export interface SettingsActions {
  // 设置更新
  updateAppSettings: (settings: Partial<SettingsState['appSettings']>) => void;
  updatePerformanceSettings: (settings: Partial<SettingsState['performanceSettings']>) => void;
  updateNetworkSettings: (settings: Partial<SettingsState['networkSettings']>) => void;
  
  // 主题操作
  setTheme: (theme: SettingsState['appSettings']['theme']) => void;
  toggleTheme: () => void;
  
  // 重置设置
  resetToDefaults: () => void;
  resetSettingsState: () => void;
}

// 初始状态
const initialState: SettingsState = {
  appSettings: {
    notifications: true,
    autoUpdate: false,
    theme: 'dark',
    language: 'zh-CN',
    cacheSize: '512MB'
  },
  performanceSettings: {
    hardwareAcceleration: true,
    backgroundThrottling: false,
    gpuRasterization: true
  },
  networkSettings: {
    timeout: 30000,
    retryAttempts: 3,
    cacheEnabled: true
  },
  settingsVersion: '1.0.0'
};

// 创建设置状态store
export const createSettingsStore = () => {
  return create<SettingsState & SettingsActions>()(
    persist(
      (set) => ({
        ...initialState,
        
        // 更新应用设置
        updateAppSettings: (settings) => set(state => ({
          appSettings: { ...state.appSettings, ...settings }
        })),
        
        // 更新性能设置
        updatePerformanceSettings: (settings) => set(state => ({
          performanceSettings: { ...state.performanceSettings, ...settings }
        })),
        
        // 更新网络设置
        updateNetworkSettings: (settings) => set(state => ({
          networkSettings: { ...state.networkSettings, ...settings }
        })),
        
        // 设置主题
        setTheme: (theme) => set(state => ({
          appSettings: { ...state.appSettings, theme }
        })),
        
        // 切换主题
        toggleTheme: () => set(state => {
          const currentTheme = state.appSettings.theme;
          const themes: SettingsState['appSettings']['theme'][] = ['light', 'dark', 'system'];
          const currentIndex = themes.indexOf(currentTheme);
          const nextIndex = (currentIndex + 1) % themes.length;
          return {
            appSettings: { ...state.appSettings, theme: themes[nextIndex] }
          };
        }),
        
        // 重置为默认设置
        resetToDefaults: () => set(initialState),
        
        // 重置设置状态
        resetSettingsState: () => set(initialState)
      }),
      {
        name: 'settings-storage',
        version: 1,
        partialize: (state) => state
      }
    )
  );
};
