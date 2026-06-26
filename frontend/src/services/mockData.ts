/** 前端 Mock 数据层.
 *
 * 与后端 mock_data.py 对应，保证前后端数据形状一致。
 * 当 VITE_USE_MOCK_DATA=true 时，api.ts 会走这里而不是 axios。
 */

export interface OverviewItem {
  station_id: number
  name: string
  capacity_kw: number
  daily_energy_kwh: number
  completion_rate: number
  loss_kwh: number
  loss_cny: number
  health_score: number
  pr: number
  status: string
}

function seededRandom(seed: string) {
  let h = 0
  for (let i = 0; i < seed.length; i++) {
    h = (h << 5) - h + seed.charCodeAt(i)
    h |= 0
  }
  return function () {
    h = (h * 9301 + 49297) % 233280
    return h / 233280
  }
}

function todaySeed(prefix: string, id: number | string) {
  const d = new Date().toISOString().slice(0, 10)
  return `${prefix}-${id}-${d}`
}

export const dashboardMock = {
  overview: async () => ({
    station_count: 6,
    online_count: 5,
    offline_count: 1,
    total_capacity_kw: 10500,
    total_active_power_kw: 4820.5,
    total_daily_energy_kwh: 32450.8,
    alarm_summary: { urgent: 2, high: 5, medium: 8, low: 3 },
    system_health: 91.2,
  }),

  stationsOverview: async (): Promise<OverviewItem[]> => {
    const names = ['河西光伏电站', '东山光伏电站', '北区分布式', '临港渔光互补', '沙漠基地一期', '山地光伏二期']
    return names.map((name, idx) => {
      const rng = seededRandom(todaySeed('overview', idx + 1))
      const capacity = 500 + idx * 300
      const completion = 0.75 + rng() * 0.2
      const theoretical = capacity * (3.8 + rng() * 1.2)
      const actual = theoretical * completion
      const loss = Math.max(0, theoretical - actual)
      return {
        station_id: idx + 1,
        name,
        capacity_kw: Math.round(capacity),
        daily_energy_kwh: Math.round(actual),
        completion_rate: Math.round(completion * 100) / 100,
        loss_kwh: Math.round(loss),
        loss_cny: Math.round(loss * 0.42),
        health_score: Math.round(70 + rng() * 28),
        pr: Math.round((0.78 + rng() * 0.14) * 100) / 100,
        status: idx === 5 ? 'inactive' : 'active',
      }
    })
  },

  riskTop: async (limit = 5): Promise<OverviewItem[]> => {
    const all = await dashboardMock.stationsOverview()
    return all.sort((a, b) => a.health_score - b.health_score).slice(0, limit)
  },

  alarmStats: async () => ({ urgent: 2, high: 5, medium: 8, low: 3 }),

  insights: async () => ({
    insight:
      '集团共 6 座场站，2 座健康度低于 80 分，今日预计损失金额 ¥12,480。建议优先处理 [山地光伏二期]（健康度 72 分）。',
  }),
}

export const alarmMock = {
  list: async () => [
    {
      id: 1,
      station_id: 1,
      device_id: 'INV001',
      level: 'critical',
      priority: 'urgent',
      title: '发电异常：辐照充足但无功率',
      description: '逆变器 INV001 辐照 823 W/m²，但功率为 0.12 kW',
      rule_name: 'power_zero_when_sunny',
      status: 'open',
      created_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    },
    {
      id: 2,
      station_id: 2,
      device_id: 'INV003',
      level: 'warning',
      priority: 'high',
      title: 'PR 偏低',
      description: '逆变器 INV003 PR 为 42.3%，低于 50%',
      rule_name: 'low_pr',
      status: 'open',
      created_at: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
    },
    {
      id: 3,
      station_id: 6,
      device_id: 'INV002',
      level: 'critical',
      priority: 'urgent',
      title: '逆变器故障码：1027',
      description: '逆变器 INV002 上报故障码 1027',
      rule_name: 'fault_code',
      status: 'acknowledged',
      created_at: new Date(Date.now() - 1000 * 60 * 58).toISOString(),
    },
    {
      id: 4,
      station_id: 3,
      device_id: 'INV001',
      level: 'warning',
      priority: 'medium',
      title: '通讯中断',
      description: '逆变器 INV001 超过 5 分钟未上报数据',
      rule_name: 'comm_interrupt',
      status: 'open',
      created_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    },
  ],

  summary: async () => [
    { rule_name: 'power_zero_when_sunny', level: 'critical', station_id: 1, count: 2, latest_at: new Date().toISOString() },
    { rule_name: 'low_pr', level: 'warning', station_id: 2, count: 3, latest_at: new Date().toISOString() },
    { rule_name: 'fault_code', level: 'critical', station_id: 6, count: 1, latest_at: new Date().toISOString() },
  ],

  close: async () => ({ success: true }),
  ack: async () => ({ success: true }),
  createWorkOrder: async (alarmId: number) => ({ success: true, data: { work_order_id: alarmId + 100, alarm_id: alarmId, status: 'pending' } }),
}

export const workOrderMock = {
  list: async () => [
    { id: 101, title: '处理告警：发电异常：辐照充足但无功率', priority: 'urgent', status: 'pending', assignee: '张工', station_id: 1, alarm_id: 1, created_at: new Date(Date.now() - 1000 * 60 * 12).toISOString() },
    { id: 102, title: '处理告警：PR 偏低', priority: 'high', status: 'in_progress', assignee: '李工', station_id: 2, alarm_id: 2, created_at: new Date(Date.now() - 1000 * 60 * 35).toISOString() },
    { id: 103, title: '定期清洗组件', priority: 'medium', status: 'completed', assignee: '王工', station_id: 3, alarm_id: null, created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString() },
  ],

  create: async (data: any) => ({ id: 200, ...data, status: 'pending', created_at: new Date().toISOString() }),

  get: async (id: number) => ({
    id,
    title: '处理告警：发电异常',
    description: '逆变器 INV001 辐照充足但无功率',
    priority: 'urgent',
    status: 'pending',
    assignee: '张工',
    station_id: 1,
    alarm_id: 1,
    feedback: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }),

  updateStatus: async (id: number, status: string, comment?: string, solution?: string) => ({
    id,
    status,
    feedback: [{ status, comment: comment || '', solution: solution || '', created_at: new Date().toISOString() }],
    updated_at: new Date().toISOString(),
  }),

  timeline: async (_id: number) => [
    { status: 'created', comment: '工单创建', created_at: new Date(Date.now() - 1000 * 60 * 60).toISOString() },
    { status: 'in_progress', comment: '已派单处理', created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString() },
    { status: 'completed', comment: '已完成', solution: '更换直流侧保险丝后恢复正常', created_at: new Date().toISOString() },
  ],

  archiveCase: async (id: number) => ({ knowledge_doc_id: id + 1000, title: `案例沉淀：处理告警 ${id}` }),
}

export const metricMock = {
  getStationMetrics: async (id: number) => {
    const rng = seededRandom(todaySeed('metrics', id))
    return {
      station_id: id,
      station_name: `电站 ${id}`,
      timestamp: new Date().toISOString(),
      active_power_kw: Math.round((400 + rng() * 600) * 100) / 100,
      daily_energy_kwh: Math.round((2000 + rng() * 1500) * 100) / 100,
      pr: Math.round((0.78 + rng() * 0.14) * 100) / 100,
      health_score: Math.round(75 + rng() * 23),
    }
  },

  getStationHistory: async (id: number, metric: string) => {
    const rng = seededRandom(`${metric}-${id}`)
    const data: { timestamp: string; value: number }[] = []
    const now = new Date()
    for (let i = 144; i >= 0; i--) {
      const ts = new Date(now.getTime() - i * 10 * 60 * 1000)
      const hour = ts.getHours() + ts.getMinutes() / 60
      let value = 0
      if (metric === 'active_power_kw') {
        if (hour >= 6 && hour <= 18) value = Math.max(0, Math.sin(((hour - 6) / 12) * Math.PI) * 800 + (rng() - 0.5) * 60)
      } else if (metric === 'irradiance_w_m2') {
        if (hour >= 6 && hour <= 18) value = Math.max(0, Math.sin(((hour - 6) / 12) * Math.PI) * 1000 + (rng() - 0.5) * 80)
      } else {
        value = rng() * 100
      }
      data.push({ timestamp: ts.toISOString(), value: Math.round(value * 100) / 100 })
    }
    return data
  },

  getStationsOverview: async () => dashboardMock.stationsOverview(),
  getStationsRanking: async (metric = 'health_score', limit = 10) => {
    const all = await dashboardMock.stationsOverview()
    const reverse = !['loss_cny', 'loss_kwh'].includes(metric)
    return all.sort((a, b) => ((a as any)[metric] - (b as any)[metric]) * (reverse ? -1 : 1)).slice(0, limit)
  },

  getStationEfficiency: async (id: number) => {
    const rng = seededRandom(todaySeed('eff', id))
    const capacity = 1000 + id * 200
    const daily = capacity * (2.5 + rng() * 2)
    const pr = 0.78 + rng() * 0.14
    return {
      station_id: id,
      capacity_kw: capacity,
      daily_energy_kwh: Math.round(daily),
      equivalent_hours: Math.round((daily / capacity) * 100) / 100,
      pr: Math.round(pr * 100) / 100,
      system_efficiency: Math.round(pr * 100 * 100) / 100,
    }
  },

  getStationLosses: async (id: number) => {
    const rng = seededRandom(todaySeed('loss', id))
    const capacity = 1000 + id * 200
    const theoretical = capacity * (3.8 + rng() * 1.2)
    const actual = theoretical * (0.78 + rng() * 0.14)
    const total = Math.max(0, theoretical - actual)
    const breakdown = [
      { name: '辐照损失', kwh: Math.round(total * 0.35), cny: Math.round(total * 0.35 * 0.42) },
      { name: '效率损失', kwh: Math.round(total * 0.3), cny: Math.round(total * 0.3 * 0.42) },
      { name: '故障损失', kwh: Math.round(total * 0.2), cny: Math.round(total * 0.2 * 0.42) },
      { name: '其他损失', kwh: Math.round(total * 0.15), cny: Math.round(total * 0.15 * 0.42) },
    ]
    return {
      station_id: id,
      theoretical_kwh: Math.round(theoretical),
      actual_kwh: Math.round(actual),
      total_loss_kwh: Math.round(total),
      total_loss_cny: Math.round(total * 0.42),
      breakdown,
    }
  },

  getStationHealthTrend: async (id: number, days = 30) => {
    const rng = seededRandom(`health-${id}`)
    const data: { date: string; health_score: number }[] = []
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(Date.now() - i * 86400000)
      data.push({ date: d.toISOString().slice(0, 10), health_score: Math.round(70 + rng() * 28) })
    }
    return data
  },

  getStationInverters: async (id: number) => {
    const rng = seededRandom(`inv-${id}`)
    return Array.from({ length: 6 }).map((_, i) => {
      const capacity = 100
      const active = capacity * (0.5 + rng() * 0.35)
      return {
        inverter_id: `INV${String(i + 1).padStart(3, '0')}`,
        name: `逆变器 ${i + 1}`,
        capacity_kw: capacity,
        active_power_kw: Math.round(active * 100) / 100,
        daily_energy_kwh: Math.round(active * 3.5 * 100) / 100,
        utilization_rate: Math.round((active / capacity) * 100) / 100,
        status: rng() > 0.85 ? 'offline' : 'online',
      }
    })
  },

  getStationStrings: async (id: number, inverterId?: string) => {
    const rng = seededRandom(`str-${id}-${inverterId || 'all'}`)
    const base = 5.0
    const strings = Array.from({ length: 12 }).map((_, i) => ({
      string_id: `STR${String(i + 1).padStart(3, '0')}`,
      name: `组串 ${i + 1}`,
      inverter_id: inverterId || `INV${String((i % 6) + 1).padStart(3, '0')}`,
      current_a: Math.round(base * (1 + (rng() - 0.5) * 0.16) * 100) / 100,
      capacity_kw: 10,
    }))
    const values = strings.map((s) => s.current_a)
    const avg = values.reduce((a, b) => a + b, 0) / values.length
    const dispersion = (Math.max(...values) - Math.min(...values)) / avg
    return strings.map((s) => ({ ...s, avg_current_a: Math.round(avg * 100) / 100, dispersion_rate: Math.round(dispersion * 100) / 100 }))
  },
}

export const reportMock = {
  list: async () => [],
  generate: async () => ({ id: 1, report_type: 'daily', created_at: new Date().toISOString() }),
  exportPdf: async () => new Blob(['PDF'], { type: 'application/pdf' }),
}

export const diagnosisMock = {
  diagnoseStation: async (id: number) => ({ id: 1, station_id: id, overall_health: 88, summary: '运行总体良好', findings: [], suggestions: [] }),
  listReports: async () => [],
  getReport: async (id: number) => ({ id, station_id: 1, overall_health: 88, summary: '运行总体良好', findings: [], suggestions: [] }),
  exportReportPdf: async () => new Blob(['PDF'], { type: 'application/pdf' }),
  createFeedback: async () => ({ success: true }),
}

export const knowledgeMock = {
  listDocuments: async () => [
    { id: 1, filename: '逆变器故障处理手册.pdf', station_id: null, status: 'active', created_at: new Date().toISOString() },
    { id: 2, filename: '光伏电站运维SOP.txt', station_id: null, status: 'active', created_at: new Date().toISOString() },
  ],
  uploadDocument: async (_file: File, _stationId?: number) => ({
    id: Date.now(),
    filename: _file.name,
    station_id: _stationId || null,
    status: 'active',
    created_at: new Date().toISOString(),
  }),
  deleteDocument: async (_id: number) => ({ success: true }),
  ask: async (question: string, _stationId?: number) => ({
    answer: `这是关于“${question}”的模拟回答。真实环境下会从知识库检索相关内容并返回。`,
    sources: [
      { content: '示例知识片段：逆变器绝缘阻抗低通常由组件或直流线缆受潮、破损引起。', metadata: { filename: '逆变器故障处理手册.pdf' } },
    ],
  }),
}

// 鉴权 / 用户 mock —— 用于无后端的演示环境（GitHub Pages）
export const authMock = {
  login: async ({ username }: { username: string; password: string }) => ({
    access_token: 'mock-token-' + Date.now(),
    user: {
      id: 1,
      username: username || 'demo',
      email: 'demo@pvops.local',
      full_name: '演示用户',
      role: 'admin',
      status: 'active',
    },
  }),
  me: async () => ({
    id: 1,
    username: 'demo',
    email: 'demo@pvops.local',
    full_name: '演示用户',
    role: 'admin',
    status: 'active',
  }),
}

// 电站 / 设备 mock —— 用于演示环境，使无后端的 Pages 也能完整导航
const DEMO_STATIONS = [
  {
    id: 1,
    name: '光伏电站 A',
    code: 'DEMO-001',
    capacity_kw: 1000,
    location: '浙江省杭州市',
    longitude: 120.16,
    latitude: 30.25,
    status: 'active',
    contact_name: '张工',
    contact_phone: '13800138000',
  },
  {
    id: 2,
    name: '光伏电站 B',
    code: 'DEMO-002',
    capacity_kw: 850,
    location: '江苏省苏州市',
    longitude: 120.62,
    latitude: 31.32,
    status: 'active',
    contact_name: '李工',
    contact_phone: '13800138001',
  },
]

const DEMO_DEVICES = (stationId: number) => [
  { id: stationId * 100 + 1, station_id: stationId, device_type: 'weather_station', device_code: 'WS001', name: '气象站 001', protocol: 'simulator', status: 'active', sort_order: 0 },
  { id: stationId * 100 + 2, station_id: stationId, device_type: 'meter', device_code: 'METER001', name: '关口表 001', protocol: 'simulator', status: 'active', sort_order: 1 },
  { id: stationId * 100 + 3, station_id: stationId, device_type: 'inverter', device_code: 'INV001', name: '逆变器 1', vendor: '阳光电源', model: 'SG350HX', protocol: 'simulator', status: 'active', sort_order: 11 },
  { id: stationId * 100 + 4, station_id: stationId, device_type: 'inverter', device_code: 'INV002', name: '逆变器 2', vendor: '阳光电源', model: 'SG350HX', protocol: 'simulator', status: 'active', sort_order: 12 },
  { id: stationId * 100 + 5, station_id: stationId, device_type: 'inverter', device_code: 'INV003', name: '逆变器 3', vendor: '阳光电源', model: 'SG350HX', protocol: 'simulator', status: 'active', sort_order: 13 },
]

export const stationMock = {
  list: async () => DEMO_STATIONS,
  get: async (id: number) => DEMO_STATIONS.find((s) => s.id === id) ?? DEMO_STATIONS[0],
}

export const deviceMock = {
  list: async (stationId?: number) => (stationId ? DEMO_DEVICES(stationId) : DEMO_DEVICES(1)),
  get: async (id: number) => DEMO_DEVICES(Math.floor(id / 100))[0] ?? DEMO_DEVICES(1)[0],
  topology: async (stationId: number) => ({
    station_id: stationId,
    devices: DEMO_DEVICES(stationId).map((d) => ({ ...d, children: [] })),
  }),
}
