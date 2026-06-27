import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 仅在 GitHub Pages 演示构建中启用：所有 API 调用走本地 mock，
// 不发任何网络请求。生产/本地开发均为 false。
//
// 该开关在 Vite 构建时被静态替换；Rollup 会把 false 分支中
// 静态引用过的 mockData 模块标记为 dead code 并 tree-shake 掉。
const USE_MOCK = import.meta.env.VITE_USE_MOCK_DATA === 'true'

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    console.error('API Error:', error)
    return Promise.reject(error)
  },
)

export default apiClient

// 动态加载 mock 模块：在 USE_MOCK=false 时这段代码不可达，
// Rollup 会随 mockData 整个文件 tree-shake 掉，不进生产 bundle。
async function loadMock() {
  return await import('./mockData')
}

export const healthApi = {
  check: async () => (USE_MOCK ? { status: 'ok' } : apiClient.get('/health')),
  ping: async () => (USE_MOCK ? { msg: 'pong' } : apiClient.get('/health/ping')),
}

export const authApi = {
  login: async (data: { username: string; password: string }) => {
    if (USE_MOCK) {
      const m = await loadMock()
      return m.authMock.login(data)
    }
    return apiClient.post('/auth/login', data)
  },
  me: async () => {
    if (USE_MOCK) {
      const m = await loadMock()
      return m.authMock.me()
    }
    return apiClient.get('/auth/me')
  },
}

export const stationApi = {
  list: async () => (USE_MOCK ? (await loadMock()).stationMock.list() : apiClient.get('/stations')),
  get: async (id: number) =>
    USE_MOCK ? (await loadMock()).stationMock.get(id) : apiClient.get(`/stations/${id}`),
  create: (data: any) => apiClient.post('/stations', data),
  update: (id: number, data: any) => apiClient.put(`/stations/${id}`, data),
  delete: (id: number) => apiClient.delete(`/stations/${id}`),
}

export const deviceApi = {
  list: async (stationId?: number, deviceType?: string) => {
    if (USE_MOCK) {
      const m = await loadMock()
      return m.deviceMock.list(stationId)
    }
    return apiClient.get('/devices', { params: { station_id: stationId, device_type: deviceType } })
  },
  get: async (id: number) =>
    USE_MOCK ? (await loadMock()).deviceMock.get(id) : apiClient.get(`/devices/${id}`),
  create: (data: any) => apiClient.post('/devices', data),
  update: (id: number, data: any) => apiClient.put(`/devices/${id}`, data),
  delete: (id: number) => apiClient.delete(`/devices/${id}`),
  topology: async (stationId: number) =>
    USE_MOCK
      ? (await loadMock()).deviceMock.topology(stationId)
      : apiClient.get(`/devices/stations/${stationId}/topology`),
}

export const dashboardApi = {
  overview: async () =>
    USE_MOCK ? (await loadMock()).dashboardMock.overview() : apiClient.get('/dashboard/overview'),
  stationsOverview: async () =>
    USE_MOCK
      ? (await loadMock()).dashboardMock.stationsOverview()
      : apiClient.get('/dashboard/stations-overview'),
  riskTop: async (limit?: number) =>
    USE_MOCK
      ? (await loadMock()).dashboardMock.riskTop(limit)
      : apiClient.get('/dashboard/risk-top', { params: { limit } }),
  alarmStats: async () =>
    USE_MOCK
      ? (await loadMock()).dashboardMock.alarmStats()
      : apiClient.get('/dashboard/alarm-stats'),
  insights: async () =>
    USE_MOCK ? (await loadMock()).dashboardMock.insights() : apiClient.get('/dashboard/insights'),
}

export const metricApi = {
  getStationMetrics: async (id: number) =>
    USE_MOCK
      ? (await loadMock()).metricMock.getStationMetrics(id)
      : apiClient.get(`/metrics/station/${id}`),
  getStationHistory: async (id: number, metric: string, start?: string, end?: string) =>
    USE_MOCK
      ? (await loadMock()).metricMock.getStationHistory(id, metric)
      : apiClient.get(`/metrics/station/${id}/history`, { params: { metric, start, end } }),
  getStationsOverview: async () =>
    USE_MOCK
      ? (await loadMock()).metricMock.getStationsOverview()
      : apiClient.get('/metrics/stations/overview'),
  getStationsRanking: async (metric?: string, limit?: number) =>
    USE_MOCK
      ? (await loadMock()).metricMock.getStationsRanking(metric, limit)
      : apiClient.get('/metrics/stations/ranking', { params: { metric, limit } }),
  getStationEfficiency: async (id: number) =>
    USE_MOCK
      ? (await loadMock()).metricMock.getStationEfficiency(id)
      : apiClient.get(`/metrics/station/${id}/efficiency`),
  getStationLosses: async (id: number) =>
    USE_MOCK
      ? (await loadMock()).metricMock.getStationLosses(id)
      : apiClient.get(`/metrics/station/${id}/losses`),
  getStationHealthTrend: async (id: number, days?: number) =>
    USE_MOCK
      ? (await loadMock()).metricMock.getStationHealthTrend(id, days)
      : apiClient.get(`/metrics/station/${id}/health-trend`, { params: { days } }),
  getStationInverters: async (id: number) =>
    USE_MOCK
      ? (await loadMock()).metricMock.getStationInverters(id)
      : apiClient.get(`/metrics/station/${id}/inverters`),
  getPeerBaseline: async (id: number) =>
    USE_MOCK
      ? (await loadMock()).metricMock.getPeerBaseline(id)
      : apiClient.get(`/metrics/station/${id}/peer-baseline`),
  getPeerRanking: async (id: number, metric?: string) =>
    USE_MOCK
      ? (await loadMock()).metricMock.getPeerRanking(id, metric)
      : apiClient.get(`/metrics/station/${id}/peer-ranking`, { params: { metric } }),
  getStationStrings: async (id: number, inverterId?: string) =>
    USE_MOCK
      ? (await loadMock()).metricMock.getStationStrings(id, inverterId)
      : apiClient.get(`/metrics/station/${id}/strings`, { params: { inverter_id: inverterId } }),
}

export const alarmApi = {
  list: async (stationId?: number, status?: string) =>
    USE_MOCK
      ? (await loadMock()).alarmMock.list()
      : apiClient.get('/alarms', { params: { station_id: stationId, status } }),
  summary: async () =>
    USE_MOCK ? (await loadMock()).alarmMock.summary() : apiClient.get('/alarms/summary'),
  close: async (id: number) =>
    USE_MOCK ? (await loadMock()).alarmMock.close() : apiClient.post(`/alarms/${id}/close`),
  ack: async (id: number) =>
    USE_MOCK ? (await loadMock()).alarmMock.ack() : apiClient.post(`/alarms/${id}/ack`),
  createWorkOrder: async (id: number, assignee?: string) =>
    USE_MOCK
      ? (await loadMock()).alarmMock.createWorkOrder(id)
      : apiClient.post(`/alarms/${id}/work-order`, { assignee }),
}

export const diagnosisApi = {
  diagnoseStation: async (stationId: number) =>
    USE_MOCK
      ? (await loadMock()).diagnosisMock.diagnoseStation(stationId)
      : apiClient.post(`/diagnosis/station/${stationId}`),
  listReports: async (stationId?: number) =>
    USE_MOCK
      ? (await loadMock()).diagnosisMock.listReports()
      : apiClient.get('/diagnosis/reports', { params: { station_id: stationId } }),
  getReport: async (id: number) =>
    USE_MOCK ? (await loadMock()).diagnosisMock.getReport(id) : apiClient.get(`/diagnosis/reports/${id}`),
  exportReportPdf: async (id: number) =>
    USE_MOCK
      ? (await loadMock()).diagnosisMock.exportReportPdf()
      : apiClient.get(`/diagnosis/reports/${id}/pdf`, { responseType: 'blob' }),
  createFeedback: async (id: number, data: { rating: string; comment?: string }) =>
    USE_MOCK
      ? (await loadMock()).diagnosisMock.createFeedback()
      : apiClient.post(`/diagnosis/reports/${id}/feedback`, data),
}

// Chat 没有本地 mock：演示环境会得到友好提示文案（来自 backend mock fallback）。
export const chatApi = {
  send: (data: { message: string; session_id?: string; context?: Record<string, any> }) =>
    apiClient.post('/chat', data),
  getHistory: (sessionId: string) => apiClient.get(`/chat/sessions/${sessionId}/history`),
}

export const knowledgeApi = {
  listDocuments: async (stationId?: number) =>
    USE_MOCK
      ? (await loadMock()).knowledgeMock.listDocuments()
      : apiClient.get('/kb/documents', { params: { station_id: stationId } }),
  uploadDocument: async (file: File, stationId?: number) => {
    if (USE_MOCK) {
      const m = await loadMock()
      return m.knowledgeMock.uploadDocument(file, stationId)
    }
    const formData = new FormData()
    formData.append('file', file)
    if (stationId) formData.append('station_id', String(stationId))
    return apiClient.post('/kb/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteDocument: async (id: number) =>
    USE_MOCK
      ? (await loadMock()).knowledgeMock.deleteDocument(id)
      : apiClient.delete(`/kb/documents/${id}`),
  ask: async (question: string, stationId?: number, topK?: number) =>
    USE_MOCK
      ? (await loadMock()).knowledgeMock.ask(question, stationId)
      : apiClient.post('/kb/ask', { question, station_id: stationId, top_k: topK }),
}

export const workOrderApi = {
  list: async (stationId?: number, status?: string) =>
    USE_MOCK
      ? (await loadMock()).workOrderMock.list()
      : apiClient.get('/workorders', { params: { station_id: stationId, status } }),
  create: async (data: {
    title: string
    description?: string
    priority?: string
    assignee?: string
    station_id?: number
    alarm_id?: number
  }) =>
    USE_MOCK ? (await loadMock()).workOrderMock.create(data) : apiClient.post('/workorders', data),
  get: async (id: number) =>
    USE_MOCK ? (await loadMock()).workOrderMock.get(id) : apiClient.get(`/workorders/${id}`),
  updateStatus: async (id: number, status: string, comment?: string, solution?: string) =>
    USE_MOCK
      ? (await loadMock()).workOrderMock.updateStatus(id, status, comment, solution)
      : apiClient.put(`/workorders/${id}`, { status, feedback_comment: comment, solution }),
  timeline: async (id: number) =>
    USE_MOCK ? (await loadMock()).workOrderMock.timeline(id) : apiClient.get(`/workorders/${id}/timeline`),
  archiveCase: async (id: number) =>
    USE_MOCK
      ? (await loadMock()).workOrderMock.archiveCase(id)
      : apiClient.post(`/workorders/${id}/archive-case`),
}

export const reportApi = {
  list: async (stationId?: number, reportType?: string) =>
    USE_MOCK
      ? (await loadMock()).reportMock.list()
      : apiClient.get('/reports', { params: { station_id: stationId, report_type: reportType } }),
  generate: async (reportType: string, stationId?: number) =>
    USE_MOCK
      ? (await loadMock()).reportMock.generate()
      : apiClient.post(`/reports/generate/${reportType}`, { station_id: stationId }),
  exportPdf: async (id: number) =>
    USE_MOCK
      ? (await loadMock()).reportMock.exportPdf()
      : apiClient.get(`/reports/${id}/pdf`, { responseType: 'blob' }),
}
