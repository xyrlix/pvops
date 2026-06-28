<template>
  <DashboardLayout>
    <template #title><span class="pv-page-title">电力市场</span></template>
    <template #subtitle>POWER TRADE · 现货价格与交易策略</template>

    <el-row :gutter="20" class="stats-row">
      <el-col v-for="c in cards" :key="c.label" :xs="12" :sm="8">
        <MetricCard
:title="c.label" :value="c.value" :unit="c.unit" :icon="c.icon"
          :icon-color="c.color" :value-color="c.color"
          :icon-bg="`linear-gradient(135deg, ${c.color}22, ${c.color}08)`"
        />
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="16">
        <PvCard title="现货价格曲线（山东节点 · 今日）" icon="TrendCharts" glow>
          <div ref="chartRef" style="height:340px" />
        </PvCard>
      </el-col>
      <el-col :xs="24" :lg="8">
        <PvCard title="AI 交易建议" icon="Cpu" glow>
          <div class="advice-list">
            <div class="advice-item advice-buy">
              <div class="advice-icon">📥</div>
              <div><strong>买入建议</strong><div class="advice-detail">06:00-07:30 低价时段充电，价 ¥0.22/kWh</div></div>
            </div>
            <div class="advice-item advice-sell">
              <div class="advice-icon">📤</div>
              <div><strong>卖出建议</strong><div class="advice-detail">17:00-19:00 晚高峰放电，价 ¥0.88/kWh</div></div>
            </div>
            <div class="advice-item advice-info">
              <div class="advice-icon">💡</div>
              <div><strong>策略说明</strong><div class="advice-detail">今日价差 0.66 元/kWh，套利空间较大</div></div>
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
  { label: '实时电价', value: '¥0.42', unit: '/kWh', icon: 'Money', color: '#34D399' },
  { label: '今日最高', value: '¥0.88', unit: '/kWh', icon: 'Top', color: '#F87171' },
  { label: '今日最低', value: '¥0.22', unit: '/kWh', icon: 'Bottom', color: '#60A5FA' },
]

const initChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const hours = Array.from({length:24}, (_,i) => `${String(i).padStart(2,'0')}:00`)
  const prices = [0.28,0.25,0.22,0.22,0.24,0.28,0.35,0.45,0.55,0.50,0.42,0.38,0.35,0.32,0.38,0.45,0.55,0.68,0.82,0.88,0.75,0.55,0.42,0.35]
  chart.setOption({
    tooltip: { trigger: 'axis', valueFormatter: (v:number) => `¥${v.toFixed(2)}/kWh` },
    grid: { left: '8%', right: '5%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', data: hours, axisLabel: { rotate: 45, color: '#94a3b8', fontSize: 10 } },
    yAxis: { type: 'value', name: '¥/kWh', axisLabel: { color: '#94a3b8' } },
    series: [{
      type: 'line', data: prices, smooth: true, areaStyle: { color: { type: 'linear', x:0, y:0, x2:0, y2:1, colorStops: [{offset:0,color:'rgba(96,165,250,0.3)'},{offset:1,color:'rgba(96,165,250,0)'.replace(')',']')}] } },
      lineStyle: { color: '#60A5FA', width: 2 }, itemStyle: { color: '#60A5FA' },
      markLine: { data: [{ yAxis: 0.42, label: { formatter: '均价 ¥0.42', color: '#94a3b8' }, lineStyle: { color: '#94a3b8', type: 'dashed' } }] },
    }],
  })
}

onMounted(() => { initChart(); window.addEventListener('resize', () => chart?.resize()) })
onUnmounted(() => { chart?.dispose(); window.removeEventListener('resize', () => chart?.resize()) })
</script>

<style scoped>
.stats-row { margin-bottom: 22px; }
.advice-list { display: flex; flex-direction: column; gap: 14px; padding: 4px 0; }
.advice-item { display: flex; gap: 10px; padding: 12px; border-radius: 10px; border: 1px solid var(--pv-border); }
.advice-icon { font-size: 20px; flex-shrink: 0; }
.advice-item strong { font-size: 14px; color: var(--pv-text-primary); }
.advice-detail { font-size: 12px; color: var(--pv-text-secondary); margin-top: 2px; }
</style>