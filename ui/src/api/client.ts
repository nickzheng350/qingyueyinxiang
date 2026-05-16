import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器
client.interceptors.request.use(
  (config) => {
    const settings = localStorage.getItem('hydraflow_api_settings')
    if (settings) {
      const { apiKey } = JSON.parse(settings)
      if (apiKey) {
        config.headers['Authorization'] = `Bearer ${apiKey}`
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.message || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export { client }
export default client