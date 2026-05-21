import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// 请求拦截器 —— 自动携带 token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器 —— 统一错误处理
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      const msg = data?.detail || data?.message || '请求失败'

      if (status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user_info')
        ElMessage.error('登录已过期，请重新登录')
        // 使用 location.href 强制页面跳转，避免在路由守卫执行期间调用 router.push
        // 导致 authStore token 未同步而产生无限重试
        window.location.href = '/login'
      } else if (status === 403) {
        ElMessage.error('权限不足')
      } else {
        ElMessage.error(msg)
      }
    } else {
      ElMessage.error('网络错误，请检查连接')
    }
    return Promise.reject(error)
  },
)

export default request
