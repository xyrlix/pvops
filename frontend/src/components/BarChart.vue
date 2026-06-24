<template>
  <div ref="chartRef" class="bar-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface BarData {
  name: string
  value: number
}

const props = defineProps<{
  data: BarData[]
  height?: number
  title?: string
  unit?: string
  color?: string
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const color = props.color || '#00f0ff'
  const sorted = [...props.data].sort((a, b) => a.value - b.value)

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(5, 9, 20, 0.92)',
      borderColor: 'rgba(0, 240, 255, 0.2)',
      textStyle: { color: '#e0faff' },
      formatter: `{b}: {c} ${props.unit || ''}`,
    },
    grid: {
      left: '3%',
      right: '8%',
      bottom: '3%',
      top: '8%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.08)' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
    },
    yAxis: {
      type: 'category',
      data: sorted.map((d) => d.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#94a3b8' },
    },
    series: [
      {
        type: 'bar',
        data: sorted.map((d) => d.value),
        barWidth: 14,
        itemStyle: {
          borderRadius: [0, 8, 8, 0],
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color },
            { offset: 1, color: `${color}55` },
          ]),
          shadowColor: color,
          shadowBlur: 12,
        },
        label: {
          show: true,
          position: 'right',
          color: '#e0faff',
          formatter: `{c}`,
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
.bar-chart {
  width: 100%;
}
</style>
