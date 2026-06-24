<template>
  <div ref="chartRef" class="bubble-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface BubbleData {
  name: string
  value: [number, number, number, number] // [capacity_kw, completion_rate, loss_cny, health_score]
}

const props = defineProps<{
  data: BubbleData[]
  height?: number
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const getColor = (health: number) => {
  if (health >= 80) return '#00ff9d'
  if (health >= 60) return '#ffcc00'
  return '#ff2a6d'
}

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const seriesData = props.data.map((d) => ({
    name: d.name,
    value: d.value,
    itemStyle: {
      color: getColor(d.value[3]),
      shadowBlur: 15,
      shadowColor: getColor(d.value[3]),
    },
  }))

  chart.setOption({
    tooltip: {
      backgroundColor: 'rgba(5, 9, 20, 0.92)',
      borderColor: 'rgba(0, 240, 255, 0.2)',
      textStyle: { color: '#e0faff' },
      formatter: (params: any) => {
        const v = params.value
        return `${params.name}<br/>
          装机容量: ${v[0]} kW<br/>
          发电完成率: ${(v[1] * 100).toFixed(1)}%<br/>
          损失金额: ¥${v[2].toFixed(0)}<br/>
          健康度: ${v[3]} 分`
      },
    },
    grid: { top: '12%', right: '8%', bottom: '12%', left: '10%' },
    xAxis: {
      type: 'value',
      name: '装机容量 (kW)',
      nameTextStyle: { color: '#64748b' },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } },
      axisLabel: { color: '#94a3b8' },
    },
    yAxis: {
      type: 'value',
      name: '发电完成率',
      nameTextStyle: { color: '#64748b' },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } },
      axisLabel: {
        color: '#94a3b8',
        formatter: (v: number) => `${(v * 100).toFixed(0)}%`,
      },
    },
    series: [
      {
        type: 'scatter',
        symbolSize: (data: number[]) => Math.max(10, Math.min(60, Math.sqrt(data[2]) / 2)),
        data: seriesData,
        emphasis: {
          focus: 'self',
          itemStyle: {
            shadowBlur: 30,
            shadowColor: '#fff',
          },
        },
      },
    ],
  })
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', () => chart?.resize())
})

watch(() => props.data, initChart, { deep: true })
</script>

<style scoped>
.bubble-chart {
  width: 100%;
}
</style>
