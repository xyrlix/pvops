<template>
  <div ref="chartRef" class="ir-power-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { metricApi } from '@/services/api'

const props = defineProps<{
  stationId: number
  height?: number
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const formatTime = (date: Date) => {
  return `${date.getMonth() + 1}/${date.getDate()} ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
}

const loadData = async () => {
  try {
    const end = new Date()
    const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)
    const [powerRes, irradianceRes] = await Promise.all([
      metricApi.getStationHistory(props.stationId, 'active_power_kw', start.toISOString(), end.toISOString()),
      metricApi.getStationHistory(props.stationId, 'irradiance_w_m2', start.toISOString(), end.toISOString()),
    ])
    const powerData = (powerRes as unknown as { timestamp: string; value: number }[]).filter((_, i) => i % 3 === 0)
    const irradianceData = (irradianceRes as unknown as { timestamp: string; value: number }[]).filter((_, i) => i % 3 === 0)

    const times = powerData.map((item) => formatTime(new Date(item.timestamp)))

    initChart(times, powerData.map((d) => d.value), irradianceData.map((d) => d.value))
  } catch (err) {
    console.error('加载辐照功率对照失败:', err)
  }
}

const initChart = (times: string[], power: number[], irradiance: number[]) => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(5, 9, 20, 0.92)',
      borderColor: 'rgba(0, 240, 255, 0.2)',
      textStyle: { color: '#e0faff' },
    },
    legend: { data: ['实时功率', '辐照度'], textStyle: { color: '#94a3b8' }, top: 0 },
    grid: { left: '3%', right: '3%', bottom: '3%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.2)' } },
      axisLabel: { color: '#94a3b8' },
    },
    yAxis: [
      {
        type: 'value',
        name: '功率(kW)',
        nameTextStyle: { color: '#64748b' },
        position: 'left',
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } },
        axisLabel: { color: '#94a3b8' },
      },
      {
        type: 'value',
        name: '辐照(W/m²)',
        nameTextStyle: { color: '#64748b' },
        position: 'right',
        splitLine: { show: false },
        axisLabel: { color: '#94a3b8' },
      },
    ],
    series: [
      {
        name: '实时功率',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: power,
        yAxisIndex: 0,
        lineStyle: { width: 3, color: '#00f0ff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 240, 255, 0.4)' },
            { offset: 1, color: 'rgba(0, 240, 255, 0)' },
          ]),
        },
      },
      {
        name: '辐照度',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: irradiance,
        yAxisIndex: 1,
        lineStyle: { width: 2, color: '#ffcc00', type: 'dashed' },
      },
    ],
  })
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', () => chart?.resize())
})

watch(() => props.stationId, loadData)
</script>

<style scoped>
.ir-power-chart {
  width: 100%;
}
</style>
