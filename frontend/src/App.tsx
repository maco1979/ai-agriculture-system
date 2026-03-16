import React, { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { QueryClientProvider } from '@tanstack/react-query'

import { MainLayout as Layout } from './components/layout/MainLayout'
import ErrorBoundary from './components/ErrorBoundary'
import { AuthProvider } from './hooks/useAuth'
import { queryClient } from './lib/query-client'
import { useOnlineStatus } from './hooks/useOnlineStatus'

import './index.css'

// 网络状态监听组件（全局生效）
function NetworkStatusMonitor() {
  // 调用hook启用网络状态监听，网络变化时自动显示toast
  useOnlineStatus()
  return null
}

// 旧路径重定向组件
function RedirectToModelDetail() {
  const params = useParams<{ id: string }>()
  return <Navigate to={`/models/${params.id}`} replace />
}

// 页面级加载占位
const PageFallback = () => (
  <div className="flex h-[60vh] items-center justify-center text-gray-400 text-sm animate-pulse">
    页面加载中...
  </div>
)

// 页面路由包装：Suspense + 独立 ErrorBoundary，防止单页崩溃影响全局
function Page({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <Suspense fallback={<PageFallback />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  )
}

const Dashboard = lazy(() => import('./pages/Dashboard').then(module => ({ default: module.Dashboard })))
const AgriculturePage = lazy(() => import('./pages/Agriculture'))
const ModelManagement = lazy(() => import('./pages/ModelManagement').then(module => ({ default: module.ModelManagement })))
const ModelDetail = lazy(() => import('./pages/ModelDetail').then(module => ({ default: module.ModelDetail })))
const InferenceService = lazy(() => import('./pages/InferenceService').then(module => ({ default: module.InferenceService })))
const Blockchain = lazy(() => import('./pages/Blockchain').then(module => ({ default: module.Blockchain })))
const FederatedLearning = lazy(() => import('./pages/FederatedLearning').then(module => ({ default: module.FederatedLearning })))
const MonitoringDashboard = lazy(() => import('./pages/MonitoringDashboard').then(module => ({ default: module.MonitoringDashboard })))
const PerformanceMonitoring = lazy(() => import('./pages/PerformanceMonitoring').then(module => ({ default: module.PerformanceMonitoring })))
const Settings = lazy(() => import('./pages/Settings').then(module => ({ default: module.Settings })))
const Community = lazy(() => import('./pages/Community'))
const AIControl = lazy(() => import('./pages/AIControl').then(module => ({ default: module.AIControl })))
const LoginPage = lazy(() => import('./pages/Login'))

function App() {
  return (
    <Router>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          {/* 全局 ErrorBoundary - 兜底保护 */}
          <ErrorBoundary>
            <Suspense fallback={<div className="flex h-screen items-center justify-center text-white">加载中...</div>}>
              <Routes>
                {/* 登录页面 - 不需要Layout */}
                <Route path="/login" element={<Page><LoginPage /></Page>} />

                {/* 受保护业务路由 */}
                <Route path="/" element={
                  <Layout><Page><Dashboard /></Page></Layout>
                } />
                <Route path="/agriculture" element={
                  <Layout><Page><AgriculturePage /></Page></Layout>
                } />
                <Route path="/models" element={
                  <Layout><Page><ModelManagement /></Page></Layout>
                } />
                <Route path="/models/:id" element={
                  <Layout><Page><ModelDetail /></Page></Layout>
                } />
                <Route path="/inference" element={
                  <Layout><Page><InferenceService /></Page></Layout>
                } />
                <Route path="/blockchain" element={
                  <Layout><Page><Blockchain /></Page></Layout>
                } />
                <Route path="/federated" element={
                  <Layout><Page><FederatedLearning /></Page></Layout>
                } />
                <Route path="/monitoring" element={
                  <Layout><Page><MonitoringDashboard /></Page></Layout>
                } />
                <Route path="/performance" element={
                  <Layout><Page><PerformanceMonitoring /></Page></Layout>
                } />
                <Route path="/settings" element={
                  <Layout><Page><Settings /></Page></Layout>
                } />
                <Route path="/community" element={
                  <Layout><Page><Community /></Page></Layout>
                } />
                <Route path="/ai-control" element={
                  <Layout><Page><AIControl /></Page></Layout>
                } />

              {/* 兼容旧路径（如 /model/:id） */}
              <Route path="/model/:id" element={<RedirectToModelDetail />} />

              {/* 重定向其他路由到首页 */}
              <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
            <Toaster 
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#1A1A1A',
                  color: '#FFFFFF',
                  border: '1px solid #2D2D2D',
                },
              }}
            />
            {/* 全局网络状态监听 */}
            <NetworkStatusMonitor />
          </ErrorBoundary>
        </QueryClientProvider>
      </AuthProvider>
    </Router>
  )
}

export default App