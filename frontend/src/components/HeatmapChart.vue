<template>
  <div ref="chartRef" class="heatmap-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface HeatPoint {
  date: string
  health_score: number
}

const props = defineProps<{
  data: HeatPoint[]
  height?: number
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const xData = props.data.map((d) => d.date.slice(5)) // MM-DD
  const values = props.data.map((d) => [d.date.slice(5), '健康度', Math.round(d.health_score)])

  chart.setOption({
    tooltip: {
      position: 'top',
      backgroundColor: 'rgba(5, 9, 20, 0.92)',
      borderColor: 'rgba(0, 240, 255, 0.2)',
      textStyle: { color: '#e0faff' },
      formatter: (params: any) => `${params.value[0]}<br/>健康度: ${params.value[2]} 分`,
    },
    grid: { top: '10%', bottom: '15%', left: '12%', right: '4%' },
    xAxis: {
      type: 'category',
      data: xData,
      splitArea: { show: false },
      axisLabel: { color: '#94a3b8', rotate: 45, fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.2)' } },
    },
    yAxis: {
      type: 'category',
      data: ['健康度'],
      axisLabel: { color: '#94a3b8' },
      axisLine: { show: false },
      splitArea: { show: false },
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: false,
      orient: 'horizontal',
      left: 'center',
      bottom: '0',
      inRange: {
        color: ['#ff2a6d', '#ffcc00', '#00ff9d'],
      },
      textStyle: { color: '#94a3b8' },
    },
    series: [
      {
        name: '健康度',
        type: 'heatmap',
        data: values,
        label: { show: true, color: '#050914', fontSize: 10, fontWeight: 'bold' },
        itemStyle: {
          borderRadius: 4,
          borderColor: 'rgba(5,9,20,0.8)',
          borderWidth: 2,
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 15,
            shadowColor: '#00f0ff',
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
.heatmap-chart {
  width: 100%;
}
</style>
