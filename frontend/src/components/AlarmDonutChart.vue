<template>
  <div ref="chartRef" class="alarm-donut" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { useChartTheme } from '@/composables/useChartTheme'

const props = defineProps<{
  data: { name: string; value: number }[]
  height?: number
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
const { resolvedTheme, colors } = useChartTheme()

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const c = colors.value
  chart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.tooltipText },
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: c.textSecondary },
    },
    series: [
      {
        type: 'pie',
        radius: ['50%', '75%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: c.tooltipBg,
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
            color: c.textPrimary,
          },
        },
        data: props.data,
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
.alarm-donut {
  width: 100%;
}
</style>
