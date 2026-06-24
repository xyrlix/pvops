export interface Station {
  id: number
  name: string
  code: string
  capacity_kw: number
  location?: string
  longitude?: number
  latitude?: number
  contact_name?: string
  contact_phone?: string
  status: string
  created_at: string
  updated_at?: string
}

export interface StationMetrics {
  station_id: number
  station_name: string
  timestamp: string
  active_power_kw: number
  daily_energy_kwh: number
  pr?: number | null
  health_score?: number | null
}

export interface MetricPoint {
  timestamp: string
  value: number
}
