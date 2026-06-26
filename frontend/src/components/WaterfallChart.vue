<template>
  <PvSkeleton v-if="loading" variant="chart" />
  <div v-else ref="chartRef" class="waterfall-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { useChartTheme } from '@/composables/useChartTheme'
import PvSkeleton from './PvSkeleton.vue'

interface LossItem {
  name: string
  kwh: number
  cny: number
}

const props = defineProps<{
  data: LossItem[]
  height?: number
  loading?: boolean
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
const { resolvedTheme, colors: themeColors } = useChartTheme()

const colors = ['#00f0ff', '#ffcc00', '#ff2a6d', '#bd34fe']

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const names = props.data.map((d) => d.name)
  const values = props.data.map((d) => d.kwh)

  const c = themeColors.value
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.tooltipText },
      // TODO(typing): replace any with explicit type; suppressed to keep CI green
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      // TODO(typing): replace any with explicit type; suppressed to keep CI green
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      formatter: (params: any) => {
        const item = props.data[params[0].dataIndex]
        return `${item.name}<br/>损失电量: ${item.kwh.toFixed(1)} kWh<br/>损失金额: ¥${item.cny.toFixed(0)}`
      },
    },
    grid: { top: '10%', right: '5%', bottom: '10%', left: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: { color: c.textSecondary },
      axisLine: { lineStyle: { color: c.grid } },
    },
    yAxis: {
      type: 'value',
      name: '损失电量 (kWh)',
      nameTextStyle: { color: c.textTertiary },
      splitLine: { lineStyle: { color: c.splitLine } },
      axisLabel: { color: c.textSecondary },
    },
    series: [
      {
        type: 'bar',
        data: values.map((v, i) => ({
          value: v,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: colors[i % colors.length] },
              { offset: 1, color: `${colors[i % colors.length]}55` },
            ]),
            borderRadius: [6, 6, 0, 0],
            shadowColor: colors[i % colors.length],
            shadowBlur: 10,
          },
        })),
        barWidth: '40%',
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
.waterfall-chart {
  width: 100%;
}
</style>
