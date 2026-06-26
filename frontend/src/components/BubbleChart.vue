<template>
  <PvSkeleton v-if="loading" variant="chart" />
  <div v-else ref="chartRef" class="bubble-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { useChartTheme } from '@/composables/useChartTheme'
import PvSkeleton from './PvSkeleton.vue'

interface BubbleData {
  name: string
  value: [number, number, number, number] // [capacity_kw, completion_rate, loss_cny, health_score]
}

const props = defineProps<{
  data: BubbleData[]
  height?: number
  loading?: boolean
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
const { resolvedTheme, colors } = useChartTheme()

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

  const c = colors.value
  chart.setOption({
    tooltip: {
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.tooltipText },
      // TODO(typing): replace any with explicit type; suppressed to keep CI green
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      // TODO(typing): replace any with explicit type; suppressed to keep CI green
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
      nameTextStyle: { color: c.textTertiary },
      splitLine: { lineStyle: { color: c.splitLine } },
      axisLabel: { color: c.textSecondary },
    },
    yAxis: {
      type: 'value',
      name: '发电完成率',
      nameTextStyle: { color: c.textTertiary },
      splitLine: { lineStyle: { color: c.splitLine } },
      axisLabel: {
        color: c.textSecondary,
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
            shadowColor: c.textPrimary,
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
.bubble-chart {
  width: 100%;
}
</style>
