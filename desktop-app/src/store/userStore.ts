import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// 用户信息类型
interface UserInfo {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar?: string;
}

// 用户状态类型
export interface UserState {
  // 认证状态
  isAuthenticated: boolean;
  isLoggingIn: boolean;
  
  // 用户信息
  user: UserInfo | null;
  
  // 认证错误
  authError: string | null;
}

// 用户操作类型
export interface UserActions {
  // 认证操作
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (userData: Partial<UserInfo> & { password: string }) => Promise<void>;
  
  // 状态更新
  setUser: (user: UserInfo | null) => void;
  setAuthError: (error: string | null) => void;
  
  // 重置状态
  resetUserState: () => void;
}

// 初始状态
const initialState: UserState = {
  isAuthenticated: false,
  isLoggingIn: false,
  user: null,
  authError: null
};

// 创建用户状态store
export const createUserStore = () => {
  return create<UserState & UserActions>()(
    persist(
      (set) => ({
        ...initialState,
        
        // 用户登录
        login: async (email) => {
          set({ isLoggingIn: true, authError: null });
          try {
            // 模拟登录请求
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // 模拟成功响应
            const user: UserInfo = {
              id: '1',
              name: '测试用户',
              email: email,
              role: 'user'
            };
            
            set({ isAuthenticated: true, user, isLoggingIn: false });
          } catch (error) {
            set({ authError: '登录失败，请检查邮箱和密码', isLoggingIn: false });
            throw error;
          }
        },
        
        // 登出操作
        logout: () => {
          set({ isAuthenticated: false, user: null });
        },
        
        // 注册操作
        register: async (userData) => {
          set({ isLoggingIn: true, authError: null });
          try {
            // 模拟注册请求
            await new Promise(resolve => setTimeout(resolve, 1200));
            
            // 模拟成功响应
            const user: UserInfo = {
              id: Date.now().toString(),
              name: userData.name || '',
              email: userData.email || '',
              role: 'user'
            };
            
            set({ isAuthenticated: true, user, isLoggingIn: false });
          } catch (error) {
            set({ authError: '注册失败，请稍后重试', isLoggingIn: false });
            throw error;
          }
        },
        
        // 状态更新
        setUser: (user) => set({ user }),
        setAuthError: (error) => set({ authError: error }),
        
        // 重置状态
        resetUserState: () => set(initialState)
      }),
      {
        name: 'user-storage',
        partialize: (state) => ({
          isAuthenticated: state.isAuthenticated,
          user: state.user
        })
      }
    )
  );
};
