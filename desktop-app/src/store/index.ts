// 状态管理入口

// 导入模块状态
import { createAppStore } from './appStore';
import { createUserStore } from './userStore';
import { createDataStore } from './dataStore';
import { createSettingsStore } from './settingsStore';

// 导出所有状态模块
export const useAppStore = createAppStore();
export const useUserStore = createUserStore();
export const useDataStore = createDataStore();
export const useSettingsStore = createSettingsStore();

// 导出类型
export type { AppState, AppActions } from './appStore';
export type { UserState, UserActions } from './userStore';
export type { DataState, DataActions } from './dataStore';
export type { SettingsState, SettingsActions } from './settingsStore';
