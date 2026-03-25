import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import toast from 'react-hot-toast'
import { API_BASE_URL, API_KEY } from '@/config'

const http: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false,
  timeout: 30000,
})

// 请求拦截器：注入 API Key（用户在 .env 中配置的云端模型 Key）
http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const headers = config.headers ?? {}

  if (API_KEY && !headers['X-API-KEY']) {
    headers['X-API-KEY'] = API_KEY
  }

  config.headers = headers
  return config
})

// 响应拦截器：统一解包 success/data 或直接返回 data
http.interceptors.response.use(
  (response: AxiosResponse) => {
    const data = response.data
    if (data && typeof data === 'object' && 'success' in data) {
      return data
    }
    return { success: true, data }
  },
  (error: AxiosError) => {
    const status = error.response?.status

    const data = error.response?.data as any
    const message = data && typeof data === 'object' && 'error' in data
      ? data.error
      : error.message || '请求失败'

    if (!status) {
      toast.error('网络异常，请检查连接')
    } else if (status >= 500) {
      toast.error(`服务器错误(${status})：${message}`)
    } else {
      toast.error(`请求失败(${status})：${message}`)
    }

    return Promise.resolve({ success: false, error: message })
  }
)

export { http }


