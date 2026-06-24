<template>
  <PvSkeleton v-if="loading" variant="chart" />
  <div v-else ref="chartRef" class="heatmap-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { useChartTheme } from '@/composables/useChartTheme'
import PvSkeleton from './PvSkeleton.vue'

interface HeatPoint {
  date: string
  health_score: number
}

const props = defineProps<{
  data: HeatPoint[]
  height?: number
  loading?: boolean
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
const { resolvedTheme, colors } = useChartTheme()

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const xData = props.data.map((d) => d.date.slice(5)) // MM-DD
  const values = props.data.map((d) => [d.date.slice(5), '健康度', Math.round(d.health_score)])

  const c = colors.value
  chart.setOption({
    tooltip: {
      position: 'top',
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.tooltipText },
      formatter: (params: any) => `${params.value[0]}<br/>健康度: ${params.value[2]} 分`,
    },
    grid: { top: '10%', bottom: '15%', left: '12%', right: '4%' },
    xAxis: {
      type: 'category',
      data: xData,
      splitArea: { show: false },
      axisLabel: { color: c.textSecondary, rotate: 45, fontSize: 10 },
      axisLine: { lineStyle: { color: c.grid } },
    },
    yAxis: {
      type: 'category',
      data: ['健康度'],
      axisLabel: { color: c.textSecondary },
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
      textStyle: { color: c.textSecondary },
    },
    series: [
      {
        name: '健康度',
        type: 'heatmap',
        data: values,
        label: { show: true, color: '#050914', fontSize: 10, fontWeight: 'bold' },
        itemStyle: {
          borderRadius: 4,
          borderColor: c.tooltipBg,
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
watch(resolvedTheme, initChart)
</script>

<style scoped>
.heatmap-chart {
  width: 100%;
}
</style>
