import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
})

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

export default api

export const fetchStock = (symbol: string, period = '1y') =>
  api.get(`/api/stocks/${symbol.toUpperCase()}?period=${period}&interval=1d`).then(r => r.data)

export const fetchFundamentals = (symbol: string) =>
  api.get(`/api/stocks/${symbol.toUpperCase()}/fundamentals`).then(r => r.data)

export const fetchPeers = (symbol: string) =>
  api.get(`/api/stocks/${symbol.toUpperCase()}/peers`).then(r => r.data)

export const searchStocks = (q: string) =>
  api.get(`/api/stocks/search/${encodeURIComponent(q)}`).then(r => r.data)

export const fetchForecast = (symbol: string, horizon = 30) =>
  api.post(`/api/forecast/${symbol.toUpperCase()}`, { horizon }).then(r => r.data)

export const fetchAnomalies = (symbol: string) =>
  api.post(`/api/anomalies/${symbol.toUpperCase()}`, {}).then(r => r.data)

export const fetchAshareStock = (symbol: string, period = '1y') =>
  api.get(`/api/ashare/${symbol}`, { params: { period } }).then(r => r.data)

export const screenStocks = (params: Record<string, unknown>) =>
  api.post('/api/screener/screen', params).then(r => r.data)

export const getPaperPortfolio = () =>
  api.get('/api/paper-trading/portfolio').then(r => r.data)

export const executePaperTrade = (trade: Record<string, unknown>) =>
  api.post('/api/paper-trading/trade', trade).then(r => r.data)
