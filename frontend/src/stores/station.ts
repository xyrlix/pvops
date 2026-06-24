import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Station, StationMetrics } from '@/types/station'
import { stationApi, metricApi } from '@/services/api'

export const useStationStore = defineStore('station', () => {
  const stations = ref<Station[]>([])
  const currentStation = ref<Station | null>(null)
  const currentMetrics = ref<StationMetrics | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchStations = async () => {
    loading.value = true
    error.value = null
    try {
      const data = (await stationApi.list()) as unknown as Station[]
      stations.value = data
    } catch (err) {
      error.value = '获取电站列表失败'
      console.error(err)
    } finally {
      loading.value = false
    }
  }

  const fetchStation = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      const data = (await stationApi.get(id)) as unknown as Station
      currentStation.value = data
    } catch (err) {
      error.value = '获取电站详情失败'
      console.error(err)
    } finally {
      loading.value = false
    }
  }

  const fetchMetrics = async (id: number) => {
    try {
      const data = (await metricApi.getStationMetrics(id)) as unknown as StationMetrics
      currentMetrics.value = data
    } catch (err) {
      console.error('获取指标失败:', err)
    }
  }

  return {
    stations,
    currentStation,
    currentMetrics,
    loading,
    error,
    fetchStations,
    fetchStation,
    fetchMetrics,
  }
})
