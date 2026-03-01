import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// 统一错误处理
http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

export default http
