<template>
  <PvSkeleton v-if="loading" variant="chart" />
  <div v-else ref="chartRef" class="donut-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { useChartTheme } from '@/composables/useChartTheme'
import PvSkeleton from './PvSkeleton.vue'

interface PieData {
  name: string
  value: number
}

const props = defineProps<{
  data: PieData[]
  height?: number
  title?: string
  loading?: boolean
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
const { resolvedTheme, colors: themeColors } = useChartTheme()

const colors = ['#00f0ff', '#00ff9d', '#ffcc00', '#ff2a6d', '#bd34fe', '#0066ff']

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const c = themeColors.value
  chart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.tooltipText },
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      bottom: '0',
      left: 'center',
      textStyle: { color: c.textSecondary },
      itemWidth: 12,
      itemHeight: 12,
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: c.tooltipBg,
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 18,
            fontWeight: 'bold',
            color: c.textPrimary,
            formatter: '{b}\n{d}%',
          },
          itemStyle: {
            shadowBlur: 20,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 240, 255, 0.5)',
          },
        },
        labelLine: { show: false },
        data: props.data.map((d, i) => ({
          ...d,
          itemStyle: { color: colors[i % colors.length] },
        })),
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
.donut-chart {
  width: 100%;
}
</style>
