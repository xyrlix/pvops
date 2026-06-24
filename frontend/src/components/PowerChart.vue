<template>
  <PvSkeleton v-if="loading" variant="chart" />
  <div v-else ref="chartRef" class="power-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { metricApi } from '@/services/api'
import { useChartTheme } from '@/composables/useChartTheme'
import PvSkeleton from './PvSkeleton.vue'

const props = defineProps<{
  stationId: number
  height?: number
  metric?: string
  title?: string
  loading?: boolean
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
const { resolvedTheme, colors } = useChartTheme()

const generateMockData = () => {
  const data = []
  const now = new Date()
  now.setHours(6, 0, 0, 0)

  for (let i = 0; i < 60; i++) {
    const time = new Date(now.getTime() + i * 10 * 60 * 1000)
    const hour = time.getHours() + time.getMinutes() / 60
    let power = 0

    if (hour >= 6 && hour <= 18) {
      const peak = Math.sin(((hour - 6) / 12) * Math.PI)
      power = peak * 800 + Math.random() * 50
    }

    data.push({
      time: formatTime(time),
      value: Number(power.toFixed(2)),
    })
  }

  return data
}

const formatTime = (date: Date) => {
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatDateTime = (date: Date) => {
  return `${date.getMonth() + 1}/${date.getDate()} ${formatTime(date)}`
}

const initChart = (data: { time: string; value: number }[], title?: string) => {
  if (!chartRef.value) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const metricName = title || '实时功率'
  const unit = props.metric === 'daily_energy_kwh' ? 'kWh' : 'kW'

  const c = colors.value
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.tooltipText },
      formatter: `{b}<br/>${metricName}: {c} ${unit}`,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map((item) => item.time),
      axisLine: { lineStyle: { color: c.grid } },
      axisLabel: { color: c.textSecondary },
    },
    yAxis: {
      type: 'value',
      name: `${metricName}(${unit})`,
      nameTextStyle: { color: c.textTertiary },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: c.splitLine } },
      axisLabel: { color: c.textSecondary },
    },
    series: [
      {
        name: metricName,
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: data.map((item) => item.value),
        lineStyle: { width: 3, color: '#00f0ff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 240, 255, 0.55)' },
            { offset: 0.5, color: 'rgba(0, 102, 255, 0.12)' },
            { offset: 1, color: 'rgba(0, 102, 255, 0)' },
          ]),
        },
        itemStyle: { color: '#00f0ff' },
        symbolSize: 8,
        emphasis: {
          itemStyle: {
            color: c.textPrimary,
            borderColor: '#00f0ff',
            borderWidth: 2,
          },
        },
      },
    ],
  })
}

const loadData = async () => {
  try {
    const metric = props.metric || 'active_power_kw'
    const end = new Date()
    const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)
    const response = await metricApi.getStationHistory(
      props.stationId,
      metric,
      start.toISOString(),
      end.toISOString()
    )
    const historyData = response as unknown as { timestamp: string; value: number }[]

    if (historyData && historyData.length > 0) {
      // 采样，避免点太多
      const sampled = historyData.filter((_, index) => index % 3 === 0)
      const data = sampled.map((item) => ({
        time: formatDateTime(new Date(item.timestamp)),
        value: item.value,
      }))
      initChart(data, props.title)
    } else {
      initChart(generateMockData(), props.title)
    }
  } catch (err) {
    console.error('加载功率曲线失败:', err)
    initChart(generateMockData(), props.title)
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', () => chart?.resize())
})

watch(() => props.stationId, () => {
  loadData()
})

watch(resolvedTheme, loadData)
</script>

<style scoped>
.power-chart {
  width: 100%;
}
</style>
