import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

export const http = axios.create({ baseURL, timeout: 15000 })

http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (!err?.response) {
      const hint = `Network Error: API недоступен по ${baseURL}. Проверьте deploy.env/.env порты и backend health.`
      return Promise.reject(new Error(hint))
    }
    const message = err?.response?.data?.detail || err.message || 'Unknown API error'
    return Promise.reject(new Error(message))
  }
)
