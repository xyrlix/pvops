<template>
  <DashboardLayout>
    <template #title>
      <span class="pv-page-title">设备分析</span>
    </template>
    <template #subtitle>DEVICE ANALYSIS</template>

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
          <PvSkeleton v-if="loadingInverters" variant="card" :rows="3" />
          <PvEmpty v-else-if="!inverters.length" description="暂无逆变器" />
          <div v-else class="inverter-grid">
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

      <!-- 群体基线对比 -->
      <el-col :xs="24" :lg="12">
        <PvCard
          :title="`群体基线 · ${peerBaseline?.capacity_bucket || ''}`"
          :subtitle="peerBaseline ? `样本数 ${peerBaseline.sample_size} 座` : ''"
          icon="Histogram"
          glow
          :loading="loadingBaseline"
        >
          <template v-if="peerBaseline && peerBaseline.sample_size > 0">
            <div class="peer-grid">
              <div class="peer-cell">
                <div class="peer-cell__label">PR</div>
                <div class="peer-cell__value" :class="peerDelta('pr')">
                  {{ formatPct(peerBaseline.self?.pr) }}
                </div>
                <div class="peer-cell__baseline">
                  行业中位 {{ formatPct(peerBaseline.median_pr) }}
                </div>
                <div class="peer-cell__top">
                  头部 P75 {{ formatPct(peerBaseline.top_quartile_pr) }}
                </div>
              </div>
              <div class="peer-cell">
                <div class="peer-cell__label">完成率</div>
                <div class="peer-cell__value" :class="peerDelta('completion_rate')">
                  {{ formatPct(peerBaseline.self?.completion_rate) }}
                </div>
                <div class="peer-cell__baseline">
                  行业中位 {{ formatPct(peerBaseline.median_completion_rate) }}
                </div>
                <div class="peer-cell__top">
                  头部 ≥ {{ formatPct((peerBaseline.median_completion_rate || 0) + 0.05) }}
                </div>
              </div>
              <div class="peer-cell">
                <div class="peer-cell__label">健康度</div>
                <div class="peer-cell__value" :class="peerDelta('health_score')">
                  {{ formatHealth(peerBaseline.self?.health_score) }}
                </div>
                <div class="peer-cell__baseline">
                  行业中位 {{ formatHealth(peerBaseline.median_health_score) }}
                </div>
                <div class="peer-cell__top">
                  头部 ≥ {{ formatHealth((peerBaseline.median_health_score || 0) + 5) }}
                </div>
              </div>
              <div class="peer-cell">
                <div class="peer-cell__label">单 kW 日发电</div>
                <div class="peer-cell__value" :class="peerDelta('daily_energy_per_kw')">
                  {{ peerBaseline.self?.daily_energy_per_kw?.toFixed(2) || '-' }}
                </div>
                <div class="peer-cell__baseline">
                  行业中位 {{ peerBaseline.median_daily_energy_per_kw?.toFixed(2) || '-' }}
                </div>
                <div class="peer-cell__top">
                  kWh / kW
                </div>
              </div>
            </div>
            <div v-if="peerRank.self_rank" class="peer-rank">
              本电站在 {{ peerRank.self_rank.capacity_bucket }} 档位内排名
              <strong>#{{ peerRank.self_rank.rank_in_bucket }}</strong> /
              {{ peerRank.self_rank.bucket_size }}，
              优于 <strong>{{ peerRank.self_rank.percentile }}%</strong> 同档电站
            </div>
          </template>
          <PvEmpty v-else description="暂无同档位基线数据" />
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
        <PvCard title="组串电流离散" icon="Connection" glow :loading="loadingStrings" :empty="!strings.length" empty-text="暂无组串数据" skeleton-variant="chart">
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
        <PvCard title="组串离散率分析" icon="DataLine" glow :loading="loadingStrings" :empty="!strings.length" empty-text="暂无组串数据">
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
import * as echarts from 'echarts'
import { useStationStore } from '@/stores/station'
import { metricApi } from '@/services/api'
import { useChartTheme } from '@/composables/useChartTheme'
import DashboardLayout from '@/components/DashboardLayout.vue'
import MetricCard from '@/components/MetricCard.vue'
import PvCard from '@/components/PvCard.vue'
import PvTag from '@/components/PvTag.vue'
import PvSkeleton from '@/components/PvSkeleton.vue'
import PvEmpty from '@/components/PvEmpty.vue'
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

interface PeerBaseline {
  capacity_bucket: string
  sample_size: number
  median_pr: number | null
  median_completion_rate: number | null
  median_health_score: number | null
  median_daily_energy_per_kw: number | null
  top_quartile_pr: number | null
  self?: {
    station_id: number
    name: string
    pr: number | null
    completion_rate: number | null
    health_score: number | null
    daily_energy_per_kw: number | null
  }
}

interface PeerRank {
  metric: string
  self_rank: {
    capacity_bucket: string
    rank_in_bucket: number
    bucket_size: number
    percentile: number
  } | null
}

const stationStore = useStationStore()
const selectedStationId = ref<number | null>(null)
const selectedInverterId = ref<string | null>(null)
const inverters = ref<InverterItem[]>([])
const strings = ref<StringItem[]>([])
const loadingInverters = ref(false)
const loadingStrings = ref(false)
const stringChartRef = ref<HTMLElement>()
let stringChart: echarts.ECharts | null = null
const { resolvedTheme: chartResolvedTheme, colors: chartColors } = useChartTheme()

// —— 群体基线 / 排名 ——
const peerBaseline = ref<PeerBaseline | null>(null)
const peerRank = ref<PeerRank>({ metric: 'health_score', self_rank: null })
const loadingBaseline = ref(false)

const formatPct = (v: number | null | undefined) => {
  if (v === null || v === undefined) return '-'
  return `${(v * 100).toFixed(1)}%`
}

const formatHealth = (v: number | null | undefined) => {
  if (v === null || v === undefined) return '-'
  return v.toFixed(1)
}

const peerDelta = (key: 'pr' | 'completion_rate' | 'health_score' | 'daily_energy_per_kw') => {
  if (!peerBaseline.value?.self || !peerBaseline.value) return ''
  const self = peerBaseline.value.self as Record<string, number | null>
  const medianKey = `median_${key}` as 'median_pr' | 'median_completion_rate' | 'median_health_score' | 'median_daily_energy_per_kw'
  const selfVal = self[key]
  const medianVal = peerBaseline.value[medianKey]
  if (selfVal === null || selfVal === undefined) return ''
  if (medianVal === null || medianVal === undefined) return ''
  if (selfVal >= medianVal * 1.05) return 'is-good'
  if (selfVal <= medianVal * 0.95) return 'is-bad'
  return 'is-mid'
}

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

  const c = chartColors.value
  const names = strings.value.map((s) => s.name || s.string_id)
  const currents = strings.value.map((s) => s.current_a)
  const avg = strings.value.length ? strings.value[0].avg_current_a : 0

  stringChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.tooltipText },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: names,
      axisLine: { lineStyle: { color: c.grid } },
      axisLabel: { color: c.textSecondary, rotate: 30 },
    },
    yAxis: {
      type: 'value',
      name: '电流(A)',
      nameTextStyle: { color: c.textTertiary },
      splitLine: { lineStyle: { color: c.splitLine } },
      axisLabel: { color: c.textSecondary },
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
  loadingInverters.value = true
  try {
    const data = (await metricApi.getStationInverters(selectedStationId.value)) as unknown as InverterItem[]
    inverters.value = data
  } catch (err) {
    console.error('加载逆变器失败:', err)
  } finally {
    loadingInverters.value = false
  }
}

const loadStrings = async () => {
  if (!selectedStationId.value) return
  loadingStrings.value = true
  try {
    const data = (await metricApi.getStationStrings(
      selectedStationId.value,
      selectedInverterId.value || undefined
    )) as unknown as StringItem[]
    strings.value = data
    initStringChart()
  } catch (err) {
    console.error('加载组串失败:', err)
  } finally {
    loadingStrings.value = false
  }
}

const loadData = async () => {
  selectedInverterId.value = null
  await Promise.all([loadInverters(), loadStrings(), loadPeerBaseline()])
}

const loadPeerBaseline = async () => {
  if (!selectedStationId.value) return
  loadingBaseline.value = true
  try {
    const [baseline, ranking] = await Promise.all([
      metricApi.getPeerBaseline(selectedStationId.value) as unknown as PeerBaseline,
      metricApi.getPeerRanking(selectedStationId.value, 'health_score') as unknown as PeerRank,
    ])
    peerBaseline.value = baseline
    peerRank.value = ranking
  } catch (err) {
    console.error('加载群体基线失败:', err)
  } finally {
    loadingBaseline.value = false
  }
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
watch(chartResolvedTheme, initStringChart)
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

.peer-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

@media (min-width: 1100px) {
  .peer-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.peer-cell {
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(96, 165, 250, 0.06);
  border: 1px solid var(--pv-border);
  text-align: center;
  transition: var(--pv-transition);
}

.peer-cell:hover {
  border-color: rgba(96, 165, 250, 0.4);
  background: rgba(96, 165, 250, 0.1);
}

.peer-cell__label {
  font-size: 11px;
  font-weight: 600;
  color: var(--pv-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 8px;
}

.peer-cell__value {
  font-family: var(--pv-font-mono);
  font-size: 22px;
  font-weight: 700;
  color: var(--pv-text-primary);
  margin-bottom: 6px;
}

.peer-cell__value.is-good {
  color: var(--pv-success);
  text-shadow: 0 0 8px rgba(52, 211, 153, 0.4);
}

.peer-cell__value.is-bad {
  color: var(--pv-danger);
  text-shadow: 0 0 8px rgba(248, 113, 113, 0.4);
}

.peer-cell__value.is-mid {
  color: var(--pv-warning);
}

.peer-cell__baseline,
.peer-cell__top {
  font-size: 11px;
  font-family: var(--pv-font-mono);
  color: var(--pv-text-tertiary);
  margin-top: 2px;
}

.peer-cell__top {
  color: var(--pv-primary);
  opacity: 0.85;
}

.peer-rank {
  margin-top: 14px;
  padding: 10px 14px;
  background: linear-gradient(90deg, rgba(167, 139, 250, 0.1), transparent);
  border-left: 3px solid var(--pv-accent);
  border-radius: 8px;
  font-size: 12px;
  color: var(--pv-text-secondary);
}

.peer-rank strong {
  color: var(--pv-accent);
  font-weight: 700;
}

.string-chart {
  width: 100%;
}
</style>
