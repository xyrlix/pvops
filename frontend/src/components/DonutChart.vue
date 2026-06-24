<template>
  <div ref="chartRef" class="donut-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface PieData {
  name: string
  value: number
}

const props = defineProps<{
  data: PieData[]
  height?: number
  title?: string
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const colors = ['#00f0ff', '#00ff9d', '#ffcc00', '#ff2a6d', '#bd34fe', '#0066ff']

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  chart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(5, 9, 20, 0.92)',
      borderColor: 'rgba(0, 240, 255, 0.2)',
      textStyle: { color: '#e0faff' },
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      bottom: '0',
      left: 'center',
      textStyle: { color: '#94a3b8' },
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
          borderColor: 'rgba(5,9,20,0.8)',
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
            color: '#f0f9ff',
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
</script>

<style scoped>
.donut-chart {
  width: 100%;
}
</style>
