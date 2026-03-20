import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const http = axios.create({ baseURL, timeout: 15000 })

http.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err?.response?.data?.detail || err.message || 'Unknown API error'
    return Promise.reject(new Error(message))
  }
)
