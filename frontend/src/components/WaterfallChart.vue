<template>
  <div ref="chartRef" class="waterfall-chart" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface LossItem {
  name: string
  kwh: number
  cny: number
}

const props = defineProps<{
  data: LossItem[]
  height?: number
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const colors = ['#00f0ff', '#ffcc00', '#ff2a6d', '#bd34fe']

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const names = props.data.map((d) => d.name)
  const values = props.data.map((d) => d.kwh)

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(5, 9, 20, 0.92)',
      borderColor: 'rgba(0, 240, 255, 0.2)',
      textStyle: { color: '#e0faff' },
      formatter: (params: any) => {
        const item = props.data[params[0].dataIndex]
        return `${item.name}<br/>损失电量: ${item.kwh.toFixed(1)} kWh<br/>损失金额: ¥${item.cny.toFixed(0)}`
      },
    },
    grid: { top: '10%', right: '5%', bottom: '10%', left: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: { color: '#94a3b8' },
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.2)' } },
    },
    yAxis: {
      type: 'value',
      name: '损失电量 (kWh)',
      nameTextStyle: { color: '#64748b' },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } },
      axisLabel: { color: '#94a3b8' },
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
</script>

<style scoped>
.waterfall-chart {
  width: 100%;
}
</style>
