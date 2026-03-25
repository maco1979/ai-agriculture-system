import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

/**
 * 本系统为开源免登录版本，/login 路由直接跳转首页。
 * App.tsx 的路由规则同样会将 /login 重定向至 /，此组件作为兜底保障。
 */
const LoginPage = () => {
  const navigate = useNavigate()

  useEffect(() => {
    navigate('/', { replace: true })
  }, [navigate])

  return null
}

export default LoginPage
