<template>
  <DashboardLayout>
    <template #breadcrumb>
      <el-icon class="back-icon" :size="22"><SetUp /></el-icon>
      <span>设备分析</span>
    </template>

    <template #actions>
      <el-select v-model="selectedStationId" placeholder="选择电站" style="width: 200px" @change="loadData">
        <el-option
          v-for="station in stationStore.stations"
          :key="station.id"
          :label="station.name"
          :value="station.id"
        />
      </el-select>
    </template>

    <!-- 指标卡 -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :xs="24" :sm="12" :md="6">
        <MetricCard
          title="逆变器数量"
          :value="inverters.length"
          unit="台"
          icon="SetUp"
          icon-color="#00f0ff"
          value-color="#00f0ff"
          icon-bg="linear-gradient(135deg, rgba(0,240,255,0.22), rgba(0,102,255,0.08))"
          :decimals="0"
        />
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <MetricCard
          title="组串数量"
          :value="strings.length"
          unit="串"
          icon="Connection"
          icon-color="#00ff9d"
          value-color="#00ff9d"
          icon-bg="linear-gradient(135deg, rgba(0,255,157,0.22), rgba(0,255,157,0.06))"
          :decimals="0"
        />
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <MetricCard
          title="平均利用率"
          :value="avgUtilization"
          unit="%"
          icon="Histogram"
          icon-color="#ffcc00"
          value-color="#ffcc00"
          icon-bg="linear-gradient(135deg, rgba(255,204,0,0.22), rgba(255,204,0,0.06))"
          :decimals="1"
        />
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <MetricCard
          title="组串离散率"
          :value="dispersionRate"
          unit="%"
          icon="WarnTriangleFilled"
          icon-color="#ff2a6d"
          value-color="#ff2a6d"
          icon-bg="linear-gradient(135deg, rgba(255,42,109,0.22), rgba(255,42,109,0.06))"
          :decimals="2"
        />
      </el-col>
    </el-row>

    <!-- 逆变器卡片 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="24">
        <PvCard title="逆变器运行状态" icon="SetUp" glow>
          <div class="inverter-grid">
            <InverterCard
              v-for="inv in inverters"
              :key="inv.inverter_id"
              :name="inv.name || inv.inverter_id"
              :active-power="inv.active_power_kw"
              :daily-energy="inv.daily_energy_kwh"
              :utilization="inv.utilization_rate"
              :status="inv.status"
            />
          </div>
        </PvCard>
      </el-col>
    </el-row>

    <!-- 逆变器对比 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="12">
        <PvCard title="逆变器日发电量对比" icon="Histogram" glow>
          <BarChart :data="inverterEnergyBars" :height="340" color="#00f0ff" unit="kWh" />
        </PvCard>
      </el-col>
      <el-col :xs="24" :lg="12">
        <PvCard title="逆变器利用率" icon="TrendCharts" glow>
          <BarChart :data="inverterUtilBars" :height="340" color="#ffcc00" unit="%" />
        </PvCard>
      </el-col>
    </el-row>

    <!-- 组串离散 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="12">
        <PvCard title="组串电流离散" icon="Connection" glow>
          <template #actions>
            <el-select v-model="selectedInverterId" clearable placeholder="全部逆变器" size="small" @change="loadStrings">
              <el-option
                v-for="inv in inverters"
                :key="inv.inverter_id"
                :label="inv.name || inv.inverter_id"
                :value="inv.inverter_id"
              />
            </el-select>
          </template>
          <div ref="stringChartRef" class="string-chart" :style="{ height: '340px' }"></div>
        </PvCard>
      </el-col>
      <el-col :xs="24" :lg="12">
        <PvCard title="组串离散率分析" icon="DataLine" glow>
          <el-table :data="strings" stripe height="340">
            <el-table-column prop="inverter_id" label="逆变器" width="110" />
            <el-table-column prop="string_id" label="组串" width="110" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="current_a" label="电流(A)" />
            <el-table-column prop="avg_current_a" label="平均电流(A)" />
            <el-table-column label="离散率">
              <template #default="{ row }">
                <PvTag :type="row.dispersion_rate > 0.05 ? 'danger' : 'success'" :label="`${(row.dispersion_rate * 100).toFixed(2)}%`" />
              </template>
            </el-table-column>
          </el-table>
        </PvCard>
      </el-col>
    </el-row>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { SetUp } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useStationStore } from '@/stores/station'
import { metricApi } from '@/services/api'
import DashboardLayout from '@/components/DashboardLayout.vue'
import MetricCard from '@/components/MetricCard.vue'
import PvCard from '@/components/PvCard.vue'
import PvTag from '@/components/PvTag.vue'
import InverterCard from '@/components/InverterCard.vue'
import BarChart from '@/components/BarChart.vue'

interface InverterItem {
  inverter_id: string
  name: string
  capacity_kw: number
  active_power_kw: number
  daily_energy_kwh: number
  utilization_rate: number
  status: string
}

interface StringItem {
  string_id: string
  name: string
  inverter_id: string
  current_a: number
  avg_current_a: number
  dispersion_rate: number
}

const stationStore = useStationStore()
const selectedStationId = ref<number | null>(null)
const selectedInverterId = ref<string | null>(null)
const inverters = ref<InverterItem[]>([])
const strings = ref<StringItem[]>([])
const stringChartRef = ref<HTMLElement>()
let stringChart: echarts.ECharts | null = null

const avgUtilization = computed(() => {
  if (!inverters.value.length) return 0
  const sum = inverters.value.reduce((acc, inv) => acc + (inv.utilization_rate || 0), 0)
  return (sum / inverters.value.length) * 100
})

const dispersionRate = computed(() => {
  if (!strings.value.length) return 0
  return (strings.value[0].dispersion_rate || 0) * 100
})

const inverterEnergyBars = computed(() =>
  inverters.value.map((inv) => ({ name: inv.name || inv.inverter_id, value: inv.daily_energy_kwh }))
)

const inverterUtilBars = computed(() =>
  inverters.value.map((inv) => ({
    name: inv.name || inv.inverter_id,
    value: Math.round((inv.utilization_rate || 0) * 100),
  }))
)

const initStringChart = () => {
  if (!stringChartRef.value) return
  if (!stringChart) stringChart = echarts.init(stringChartRef.value)

  const names = strings.value.map((s) => s.name || s.string_id)
  const currents = strings.value.map((s) => s.current_a)
  const avg = strings.value.length ? strings.value[0].avg_current_a : 0

  stringChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(5, 9, 20, 0.92)',
      borderColor: 'rgba(0, 240, 255, 0.2)',
      textStyle: { color: '#e0faff' },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: names,
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.2)' } },
      axisLabel: { color: '#94a3b8', rotate: 30 },
    },
    yAxis: {
      type: 'value',
      name: '电流(A)',
      nameTextStyle: { color: '#64748b' },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } },
      axisLabel: { color: '#94a3b8' },
    },
    series: [
      {
        type: 'bar',
        data: currents.map((v) => ({
          value: v,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: v > avg * 1.1 || v < avg * 0.9 ? '#ff2a6d' : '#00ff9d' },
              { offset: 1, color: v > avg * 1.1 || v < avg * 0.9 ? '#ff2a6d55' : '#00ff9d55' },
            ]),
            borderRadius: [6, 6, 0, 0],
          },
        })),
        barWidth: '40%',
        markLine: avg
          ? {
              data: [{ yAxis: avg, name: '平均电流' }],
              lineStyle: { color: '#ffcc00', type: 'dashed' },
              label: { color: '#ffcc00', formatter: '平均 {c}A' },
            }
          : undefined,
      },
    ],
  })
}

const loadInverters = async () => {
  if (!selectedStationId.value) return
  try {
    const data = (await metricApi.getStationInverters(selectedStationId.value)) as unknown as InverterItem[]
    inverters.value = data
  } catch (err) {
    console.error('加载逆变器失败:', err)
  }
}

const loadStrings = async () => {
  if (!selectedStationId.value) return
  try {
    const data = (await metricApi.getStationStrings(
      selectedStationId.value,
      selectedInverterId.value || undefined
    )) as unknown as StringItem[]
    strings.value = data
    initStringChart()
  } catch (err) {
    console.error('加载组串失败:', err)
  }
}

const loadData = async () => {
  selectedInverterId.value = null
  await Promise.all([loadInverters(), loadStrings()])
}

onMounted(() => {
  stationStore.fetchStations().then(() => {
    const demo = stationStore.stations.find((s) => s.code === 'DEMO-001')
    selectedStationId.value = demo?.id || stationStore.stations[0]?.id || null
    if (selectedStationId.value) loadData()
  })
  window.addEventListener('resize', () => stringChart?.resize())
})

onUnmounted(() => {
  stringChart?.dispose()
  window.removeEventListener('resize', () => stringChart?.resize())
})

watch(() => strings.value, initStringChart, { deep: true })
</script>

<style scoped>
.metrics-row {
  margin-bottom: 22px;
}

.chart-row {
  margin-bottom: 22px;
}

.inverter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 18px;
}

.string-chart {
  width: 100%;
}
</style>
