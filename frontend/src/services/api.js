import axios from 'axios'

const API_BASE_URL = 'http://localhost:8081/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  signup: (username, email, password) => api.post('/auth/signup', { username, email, password }),
}

export const monitoringAPI = {
  getPackets: (limit = 50) => api.get(`/packets?limit=${limit}`),
  searchPackets: (query) => api.get(`/packets/search?query=${query}`),
  filterPackets: (filters) => api.get('/packets/filter', { params: filters }),
  getStats: () => api.get('/stats'),
  getRecentAlerts: (limit = 10) => api.get(`/alerts?limit=${limit}`),
}

export const analyticsAPI = {
  getAttackDistribution: () => api.get('/analytics/attack-distribution'),
  getTrafficTrends: (timeRange = '24h') => api.get(`/analytics/traffic-trends?range=${timeRange}`),
  getThreatHeatmap: () => api.get('/analytics/threat-heatmap'),
  getDetectionStats: () => api.get('/analytics/detection-stats'),
}

export const logsAPI = {
  getLogs: (page = 1, limit = 50) => api.get(`/logs?page=${page}&limit=${limit}`),
  exportLogs: () => api.get('/logs/export', { responseType: 'blob' }),
  clearLogs: () => api.delete('/logs'),
  searchLogs: (query) => api.get(`/logs/search?query=${query}`),
}

export const settingsAPI = {
  getSettings: () => api.get('/settings'),
  updateSettings: (settings) => api.put('/settings', settings),
  startMonitoring: () => api.post('/monitoring/start'),
  stopMonitoring: () => api.post('/monitoring/stop'),
  getMonitoringStatus: () => api.get('/monitoring/status'),
}

export default api
