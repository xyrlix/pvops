<template>
  <DashboardLayout>
    <template #title><span class="pv-page-title">储能监控</span></template>
    <template #subtitle>ENERGY STORAGE · 充放电策略与状态</template>

    <el-row :gutter="20" class="stats-row">
      <el-col v-for="c in cards" :key="c.label" :xs="12" :sm="6">
        <MetricCard
          :title="c.label" :value="c.value" :unit="c.unit" :icon="c.icon"
          :icon-color="c.color" :value-color="c.color"
          :icon-bg="`linear-gradient(135deg, ${c.color}22, ${c.color}08)`"
        />
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="14">
        <PvCard title="充放电曲线（近 7 天）" icon="TrendCharts" glow>
          <div ref="chartRef" style="height:320px" />
        </PvCard>
      </el-col>
      <el-col :xs="24" :lg="10">
        <PvCard title="明日 AI 策略" icon="Cpu" glow>
          <div class="strategy-panel">
            <div class="strategy-item">
              <div class="strategy-time">00:00-06:00</div>
              <el-tag type="success" effect="dark">充电 ¥0.25/kWh</el-tag>
            </div>
            <div class="strategy-item">
              <div class="strategy-time">06:00-10:00</div>
              <el-tag>待机</el-tag>
            </div>
            <div class="strategy-item">
              <div class="strategy-time">10:00-15:00</div>
              <el-tag type="warning">光伏充电</el-tag>
            </div>
            <div class="strategy-item">
              <div class="strategy-time">15:00-21:00</div>
              <el-tag type="danger">放电 ¥0.85/kWh</el-tag>
            </div>
            <div class="strategy-item">
              <div class="strategy-time">21:00-24:00</div>
              <el-tag type="success">充电 ¥0.28/kWh</el-tag>
            </div>
            <el-divider />
            <div style="text-align:center">
              <div class="strategy-profit">预计日收益 <strong>¥1,250</strong></div>
              <div style="font-size:12px;color:var(--pv-text-tertiary)">较昨日 +8.2% · 月累计 ¥31,800</div>
            </div>
          </div>
        </PvCard>
      </el-col>
    </el-row>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import DashboardLayout from '@/components/DashboardLayout.vue'
import PvCard from '@/components/PvCard.vue'
import MetricCard from '@/components/MetricCard.vue'

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const cards = [
  { label: 'SOC 荷电状态', value: 68, unit: '%', icon: 'Battery', color: '#34D399' },
  { label: 'SOH 健康度', value: 92, unit: '%', icon: 'FirstAidKit', color: '#60A5FA' },
  { label: '充放电功率', value: 125, unit: 'kW', icon: 'Lightning', color: '#FBBF24' },
  { label: '循环次数', value: 1280, unit: '次', icon: 'Refresh', color: '#A78BFA' },
]

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '8%', right: '5%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', data: ['06/21','06/22','06/23','06/24','06/25','06/26','06/27'], axisLabel: { color: '#94a3b8' } },
    yAxis: [{ type: 'value', name: '功率(kW)', axisLabel: { color: '#94a3b8' } }, { type: 'value', name: 'SOC(%)', axisLabel: { color: '#94a3b8' } }],
    series: [
      { name: '充电', type: 'bar', stack: 'power', data: [80,60,90,70,85,95,75], itemStyle: { color: '#34D399' }, yAxisIndex: 0 },
      { name: '放电', type: 'bar', stack: 'power', data: [-60,-45,-70,-55,-65,-80,-60], itemStyle: { color: '#F87171' }, yAxisIndex: 0 },
      { name: 'SOC', type: 'line', data: [55,65,60,70,68,72,68], itemStyle: { color: '#60A5FA' }, yAxisIndex: 1 },
    ],
    legend: { textStyle: { color: '#94a3b8' } },
  })
}

onMounted(() => { initChart(); window.addEventListener('resize', () => chart?.resize()) })
onUnmounted(() => { chart?.dispose(); window.removeEventListener('resize', () => chart?.resize()) })
</script>

<style scoped>
.stats-row { margin-bottom: 22px; }
.strategy-panel { padding: 8px 0; }
.strategy-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; }
.strategy-time { font-family: var(--pv-font-mono); font-size: 13px; font-weight: 600; color: var(--pv-text-primary); }
.strategy-profit { font-size: 20px; font-weight: 700; color: var(--pv-success); font-family: var(--pv-font-mono); margin: 6px 0 4px; }
</style>