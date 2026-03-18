import React from 'react'
import { AlertTriangle, ServerCrash, WifiOff, RefreshCw, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
  errorType?: 'network' | 'render' | 'unknown'
}

/** 判断错误类型 */
function classifyError(error: Error): 'network' | 'render' | 'unknown' {
  const msg = error.message?.toLowerCase() ?? ''
  if (msg.includes('network') || msg.includes('fetch') || msg.includes('连接')) return 'network'
  return 'render'
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
      errorType: classifyError(error)
    }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary] 捕获渲染错误', error, info)
  }

  handleReload = () => {
    this.setState({ hasError: false, error: undefined, errorType: undefined })
    window.location.reload()
  }

  handleGoHome = () => {
    this.setState({ hasError: false, error: undefined, errorType: undefined })
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return <>{this.props.fallback}</>

      const { errorType, error } = this.state
      const isNetwork = errorType === 'network'

      return (
        <div className="flex h-screen flex-col items-center justify-center space-y-6 bg-[#0b0b0f] text-white px-6 text-center">
          {/* 图标区 */}
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-red-500/10 blur-2xl" />
            <div className="relative flex h-20 w-20 items-center justify-center rounded-full border border-red-500/30 bg-red-500/10">
              {isNetwork ? (
                <WifiOff className="h-9 w-9 text-red-400" />
              ) : (
                <ServerCrash className="h-9 w-9 text-red-400" />
              )}
            </div>
          </div>

          {/* 标题 */}
          <div className="space-y-2">
            <div className="flex items-center justify-center space-x-2 text-red-400">
              <AlertTriangle className="h-5 w-5" />
              <span className="text-xl font-bold">
                {isNetwork ? '网络连接异常' : '页面发生错误'}
              </span>
            </div>
            <p className="text-sm text-gray-400 max-w-sm">
              {isNetwork
                ? '无法连接到服务器，请检查网络连接或稍后重试。'
                : '页面遇到了意外错误，您可以尝试刷新或返回首页。'}
            </p>
          </div>

          {/* 错误详情（折叠显示） */}
          {error && (
            <details className="max-w-lg text-left">
              <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-300 transition-colors">
                查看错误详情
              </summary>
              <pre className="mt-2 rounded-lg border border-gray-700 bg-gray-900/60 p-3 text-xs text-red-300 overflow-auto max-h-32 whitespace-pre-wrap break-words">
                {error.stack ?? error.message}
              </pre>
            </details>
          )}

          {/* 操作按钮 */}
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={this.handleGoHome}
              className="gap-2 border-gray-600 text-gray-300 hover:border-gray-400 hover:text-white"
            >
              <Home className="h-4 w-4" />
              返回首页
            </Button>
            <Button
              variant="tech"
              onClick={this.handleReload}
              className="gap-2 min-w-[120px]"
            >
              <RefreshCw className="h-4 w-4" />
              刷新页面
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary


/** ===================================================================
 *  API 错误反馈组件
 *  用于在页面内局部展示 API 404/500 错误，而不触发全屏 ErrorBoundary
 * =================================================================== */
interface ApiErrorCardProps {
  status?: number
  message?: string
  onRetry?: () => void
  className?: string
}

export function ApiErrorCard({ status, message, onRetry, className = '' }: ApiErrorCardProps) {
  const is404 = status === 404
  const is500 = status != null && status >= 500

  const title = is404
    ? '资源未找到 (404)'
    : is500
    ? `服务器错误 (${status})`
    : message
    ? '请求失败'
    : '数据加载失败'

  const hint = is404
    ? '请求的资源不存在，可能已被删除或路径有误。'
    : is500
    ? '后端服务出现错误，请稍后重试或联系管理员。'
    : message ?? '请稍后再试。'

  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-8 text-center ${className}`}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full border border-red-500/30 bg-red-500/10">
        {is404 ? (
          <AlertTriangle className="h-6 w-6 text-red-400" />
        ) : (
          <ServerCrash className="h-6 w-6 text-red-400" />
        )}
      </div>
      <div className="space-y-1">
        <p className="font-semibold text-red-400">{title}</p>
        <p className="text-sm text-gray-400 max-w-xs">{hint}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-1 flex items-center gap-1.5 rounded-lg border border-gray-600 bg-transparent px-4 py-1.5 text-sm text-gray-300 hover:border-gray-400 hover:text-white transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          重试
        </button>
      )}
    </div>
  )
}
