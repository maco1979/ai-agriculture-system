import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import toast from 'react-hot-toast'
import { API_BASE_URL, API_KEY } from '@/config'

const http: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false,
  timeout: 15000,
})

// 请求拦截器：注入 API Key
http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const headers = config.headers ?? {}
  if (API_KEY && !headers['X-API-KEY']) {
    headers['X-API-KEY'] = API_KEY
  }
  config.headers = headers
  return config
})

// 静默重试：网络错误自动重试一次，避免启动时短暂连接失败刷屏 toast
const RETRY_FLAG = '__retried'
http.interceptors.response.use(
  (response: AxiosResponse) => {
    const data = response.data
    if (data && typeof data === 'object' && 'success' in data) {
      return data
    }
    return { success: true, data }
  },
  async (error: AxiosError) => {
    const config = error.config as any
    const status = error.response?.status

    // 网络层错误（无 status）且还没重试过 → 静默重试一次
    if (!status && !config?.[RETRY_FLAG]) {
      config[RETRY_FLAG] = true
      try {
        const retryRes = await http.request(config)
        return retryRes
      } catch {
        // 重试仍失败，才弹 toast（延迟一下避免启动闪烁）
        setTimeout(() => toast.error('无法连接到服务器，请检查网络连接或稍后重试。'), 300)
        return Promise.resolve({ success: false, error: '网络连接失败' })
      }
    }

    const data = error.response?.data as any
    const message = data && typeof data === 'object' && 'error' in data
      ? data.error
      : error.message || '请求失败'

    if (!status) {
      // 已重试过，不重复弹
    } else if (status >= 500) {
      toast.error(`服务器错误(${status})：${message}`)
    } else if (status !== 404) {
      // 404 静默处理（接口不存在不需要打扰用户）
      toast.error(`请求失败(${status})：${message}`)
    }

    return Promise.resolve({ success: false, error: message })
  }
)

export { http }


