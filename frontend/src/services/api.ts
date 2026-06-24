import axios from 'axios'
import * as mockData from './mockData'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

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

export const healthApi = {
  check: () => (USE_MOCK ? Promise.resolve({ status: 'ok' }) : apiClient.get('/health')),
  ping: () => (USE_MOCK ? Promise.resolve({ msg: 'pong' }) : apiClient.get('/health/ping')),
}

export const authApi = {
  login: (data: { username: string; password: string }) => apiClient.post('/auth/login', data),
  me: () => apiClient.get('/auth/me'),
}

export const stationApi = {
  list: () => apiClient.get('/stations'),
  get: (id: number) => apiClient.get(`/stations/${id}`),
  create: (data: any) => apiClient.post('/stations', data),
  update: (id: number, data: any) => apiClient.put(`/stations/${id}`, data),
  delete: (id: number) => apiClient.delete(`/stations/${id}`),
}

export const deviceApi = {
  list: (stationId?: number, deviceType?: string) =>
    apiClient.get('/devices', { params: { station_id: stationId, device_type: deviceType } }),
  get: (id: number) => apiClient.get(`/devices/${id}`),
  create: (data: any) => apiClient.post('/devices', data),
  update: (id: number, data: any) => apiClient.put(`/devices/${id}`, data),
  delete: (id: number) => apiClient.delete(`/devices/${id}`),
  topology: (stationId: number) => apiClient.get(`/devices/stations/${stationId}/topology`),
}

export const dashboardApi = {
  overview: () => (USE_MOCK ? mockData.dashboardMock.overview() : apiClient.get('/dashboard/overview')),
  stationsOverview: () => (USE_MOCK ? mockData.dashboardMock.stationsOverview() : apiClient.get('/dashboard/stations-overview')),
  riskTop: (limit?: number) => (USE_MOCK ? mockData.dashboardMock.riskTop(limit) : apiClient.get('/dashboard/risk-top', { params: { limit } })),
  alarmStats: () => (USE_MOCK ? mockData.dashboardMock.alarmStats() : apiClient.get('/dashboard/alarm-stats')),
  insights: () => (USE_MOCK ? mockData.dashboardMock.insights() : apiClient.get('/dashboard/insights')),
}

export const metricApi = {
  getStationMetrics: (id: number) =>
    USE_MOCK ? mockData.metricMock.getStationMetrics(id) : apiClient.get(`/metrics/station/${id}`),
  getStationHistory: (id: number, metric: string, start?: string, end?: string) =>
    USE_MOCK
      ? mockData.metricMock.getStationHistory(id, metric)
      : apiClient.get(`/metrics/station/${id}/history`, {
          params: { metric, start, end },
        }),
  getStationsOverview: () =>
    USE_MOCK ? mockData.metricMock.getStationsOverview() : apiClient.get('/metrics/stations/overview'),
  getStationsRanking: (metric?: string, limit?: number) =>
    USE_MOCK
      ? mockData.metricMock.getStationsRanking(metric, limit)
      : apiClient.get('/metrics/stations/ranking', { params: { metric, limit } }),
  getStationEfficiency: (id: number) =>
    USE_MOCK ? mockData.metricMock.getStationEfficiency(id) : apiClient.get(`/metrics/station/${id}/efficiency`),
  getStationLosses: (id: number) =>
    USE_MOCK ? mockData.metricMock.getStationLosses(id) : apiClient.get(`/metrics/station/${id}/losses`),
  getStationHealthTrend: (id: number, days?: number) =>
    USE_MOCK
      ? mockData.metricMock.getStationHealthTrend(id, days)
      : apiClient.get(`/metrics/station/${id}/health-trend`, { params: { days } }),
  getStationInverters: (id: number) =>
    USE_MOCK ? mockData.metricMock.getStationInverters(id) : apiClient.get(`/metrics/station/${id}/inverters`),
  getStationStrings: (id: number, inverterId?: string) =>
    USE_MOCK
      ? mockData.metricMock.getStationStrings(id, inverterId)
      : apiClient.get(`/metrics/station/${id}/strings`, { params: { inverter_id: inverterId } }),
}

export const alarmApi = {
  list: (stationId?: number, status?: string) =>
    USE_MOCK
      ? mockData.alarmMock.list()
      : apiClient.get('/alarms', {
          params: { station_id: stationId, status },
        }),
  summary: () => (USE_MOCK ? mockData.alarmMock.summary() : apiClient.get('/alarms/summary')),
  close: (id: number) => (USE_MOCK ? mockData.alarmMock.close() : apiClient.post(`/alarms/${id}/close`)),
  ack: (id: number) => (USE_MOCK ? mockData.alarmMock.ack() : apiClient.post(`/alarms/${id}/ack`)),
  createWorkOrder: (id: number, assignee?: string) =>
    USE_MOCK
      ? mockData.alarmMock.createWorkOrder(id)
      : apiClient.post(`/alarms/${id}/work-order`, { assignee }),
}

export const diagnosisApi = {
  diagnoseStation: (stationId: number) =>
    USE_MOCK
      ? mockData.diagnosisMock.diagnoseStation(stationId)
      : apiClient.post(`/diagnosis/station/${stationId}`),
  listReports: (stationId?: number) =>
    USE_MOCK
      ? mockData.diagnosisMock.listReports()
      : apiClient.get('/diagnosis/reports', {
          params: { station_id: stationId },
        }),
  getReport: (id: number) =>
    USE_MOCK ? mockData.diagnosisMock.getReport(id) : apiClient.get(`/diagnosis/reports/${id}`),
  exportReportPdf: (id: number) =>
    USE_MOCK
      ? mockData.diagnosisMock.exportReportPdf()
      : apiClient.get(`/diagnosis/reports/${id}/pdf`, { responseType: 'blob' }),
  createFeedback: (id: number, data: { rating: string; comment?: string }) =>
    USE_MOCK
      ? mockData.diagnosisMock.createFeedback()
      : apiClient.post(`/diagnosis/reports/${id}/feedback`, data),
}

export const chatApi = {
  send: (data: { message: string; session_id?: string; context?: Record<string, any> }) =>
    apiClient.post('/chat', data),
  getHistory: (sessionId: string) => apiClient.get(`/chat/sessions/${sessionId}/history`),
}

export const knowledgeApi = {
  listDocuments: (stationId?: number) =>
    apiClient.get('/kb/documents', { params: { station_id: stationId } }),
  uploadDocument: (file: File, stationId?: number) => {
    const formData = new FormData()
    formData.append('file', file)
    if (stationId) formData.append('station_id', String(stationId))
    return apiClient.post('/kb/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteDocument: (id: number) => apiClient.delete(`/kb/documents/${id}`),
  ask: (question: string, stationId?: number, topK?: number) =>
    apiClient.post('/kb/ask', { question, station_id: stationId, top_k: topK }),
}

export const workOrderApi = {
  list: (stationId?: number, status?: string) =>
    USE_MOCK
      ? mockData.workOrderMock.list()
      : apiClient.get('/workorders', {
          params: { station_id: stationId, status },
        }),
  create: (data: {
    title: string
    description?: string
    priority?: string
    assignee?: string
    station_id?: number
    alarm_id?: number
  }) => (USE_MOCK ? mockData.workOrderMock.create(data) : apiClient.post('/workorders', data)),
  get: (id: number) => (USE_MOCK ? mockData.workOrderMock.get(id) : apiClient.get(`/workorders/${id}`)),
  updateStatus: (id: number, status: string, comment?: string, solution?: string) =>
    USE_MOCK
      ? mockData.workOrderMock.updateStatus(id, status, comment, solution)
      : apiClient.put(`/workorders/${id}`, { status, feedback_comment: comment, solution }),
  timeline: (id: number) =>
    USE_MOCK ? mockData.workOrderMock.timeline(id) : apiClient.get(`/workorders/${id}/timeline`),
  archiveCase: (id: number) =>
    USE_MOCK
      ? mockData.workOrderMock.archiveCase(id)
      : apiClient.post(`/workorders/${id}/archive-case`),
}

export const reportApi = {
  list: (stationId?: number, reportType?: string) =>
    USE_MOCK
      ? mockData.reportMock.list()
      : apiClient.get('/reports', {
          params: { station_id: stationId, report_type: reportType },
        }),
  generate: (reportType: string, stationId?: number) =>
    USE_MOCK
      ? mockData.reportMock.generate()
      : apiClient.post(`/reports/generate/${reportType}`, { station_id: stationId }),
}
