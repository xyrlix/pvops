<template>
  <div ref="chartRef" class="gauge-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  value: number
  height?: number
  title?: string
  unit?: string
  max?: number
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const getColor = (value: number, max: number) => {
  const ratio = value / max
  if (ratio >= 0.8) return '#00ff9d'
  if (ratio >= 0.5) return '#ffcc00'
  return '#ff2a6d'
}

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const max = props.max || 100
  const color = getColor(props.value, max)

  chart.setOption({
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max,
        radius: '90%',
        center: ['50%', '55%'],
        splitNumber: 5,
        itemStyle: {
          color,
          shadowColor: color,
          shadowBlur: 20,
        },
        progress: {
          show: true,
          roundCap: true,
          width: 14,
        },
        pointer: {
          icon: 'path://M2090.36389,615.30999 L2090.36389,615.30999 C2091.48372,615.30999 2092.40383,616.194028 2092.44859,617.312956 L2096.90698,728.755929 C2097.05155,732.369577 2094.8143,735.675246 2091.28487,737.0004 C2087.75544,738.325554 2083.75037,737.307491 2081.373,734.754446 L1996.875,640.946894 C1994.445,638.327459 1994.445,634.280345 1996.875,631.66091 L2081.373,537.853358 C2083.75037,535.300313 2087.75544,534.28225 2091.28487,535.607404 C2094.8143,536.932558 2097.05155,540.238227 2096.90698,543.851875 L2092.44859,655.294848 C2092.40383,656.413776 2091.48372,657.297814 2090.36389,657.297814 L2090.36389,657.297814 Z',
          length: '60%',
          width: 8,
          offsetCenter: [0, '5%'],
          itemStyle: {
            color: '#fff',
            shadowColor: color,
            shadowBlur: 15,
          },
        },
        axisLine: {
          roundCap: true,
          lineStyle: {
            width: 14,
            color: [[1, 'rgba(148,163,184,0.12)']],
          },
        },
        axisTick: { show: false },
        splitLine: {
          length: 8,
          lineStyle: {
            width: 2,
            color: 'rgba(148,163,184,0.2)',
          },
        },
        axisLabel: {
          distance: 22,
          color: '#94a3b8',
          fontSize: 11,
        },
        title: {
          offsetCenter: [0, '82%'],
          fontSize: 13,
          color: '#94a3b8',
        },
        detail: {
          valueAnimation: true,
          fontSize: 30,
          fontWeight: 'bold',
          offsetCenter: [0, '35%'],
          formatter: `{value}${props.unit || ''}`,
          color: '#f0f9ff',
          textShadowBlur: 10,
          textShadowColor: color,
        },
        data: [{ value: props.value, name: props.title || '' }],
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

watch(() => props.value, initChart)
</script>

<style scoped>
.gauge-chart {
  width: 100%;
}
</style>
