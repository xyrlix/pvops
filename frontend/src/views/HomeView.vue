<template>
  <DashboardLayout>
    <template #breadcrumb>
      <el-icon class="back-icon" :size="22"><Odometer /></el-icon>
      <span>总览大屏</span>
    </template>

    <!-- AI 洞察 -->
    <el-row :gutter="20" class="insight-row">
      <el-col :span="24">
        <div class="ai-insight-bar" @click="copilotStore.open({ type: 'overview' })">
          <el-icon class="insight-icon" :size="24"><Cpu /></el-icon>
          <div class="insight-content">
            <span class="insight-label">AI 洞察</span>
            <span class="insight-text">{{ aiInsight }}</span>
          </div>
          <el-icon class="insight-arrow"><ArrowRight /></el-icon>
        </div>
      </el-col>
    </el-row>

    <!-- 顶部 KPI -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :xs="24" :sm="12" :md="6">
        <MetricCard
          title="电站总数"
          :value="overviewKpi.station_count"
          unit="座"
          icon="OfficeBuilding"
          icon-color="#00f0ff"
          value-color="#00f0ff"
          icon-bg="linear-gradient(135deg, rgba(0,240,255,0.22), rgba(0,102,255,0.08))"
          :trend="2.4"
          :loading="kpiLoading"
        />
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <MetricCard
          title="总装机容量"
          :value="overviewKpi.total_capacity_kw"
          unit="kW"
          icon="Lightning"
          icon-color="#00ff9d"
          value-color="#00ff9d"
          icon-bg="linear-gradient(135deg, rgba(0,255,157,0.22), rgba(0,255,157,0.06))"
          :loading="kpiLoading"
        />
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <MetricCard
          title="实时总功率"
          :value="overviewKpi.total_active_power_kw"
          unit="kW"
          icon="TrendCharts"
          icon-color="#ffcc00"
          value-color="#ffcc00"
          icon-bg="linear-gradient(135deg, rgba(255,204,0,0.22), rgba(255,204,0,0.06))"
          :trend="-1.2"
          :loading="kpiLoading"
        />
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <MetricCard
          title="今日总发电"
          :value="overviewKpi.total_daily_energy_kwh"
          unit="kWh"
          icon="Calendar"
          icon-color="#ff2a6d"
          value-color="#ff2a6d"
          icon-bg="linear-gradient(135deg, rgba(255,42,109,0.22), rgba(255,42,109,0.06))"
          :trend="5.8"
          :loading="kpiLoading"
        />
      </el-col>
    </el-row>

    <!-- 告警统计 -->
    <el-row :gutter="20" class="alarm-stats-row">
      <el-col :xs="12" :sm="6" :md="3" v-for="item in alarmStatsList" :key="item.key">
        <div class="alarm-stat-card" :class="item.key" @click="$router.push('/alarms')">
          <div class="alarm-stat-value">{{ item.value }}</div>
          <div class="alarm-stat-label">{{ item.label }}</div>
          <div class="alarm-stat-bar" />
        </div>
      </el-col>
    </el-row>

    <!-- 气泡图 + 高风险 TOP -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="16">
        <PvCard title="集团场站分布" subtitle="气泡大小 = 损失金额，颜色 = 健康度" icon="Coordinate" glow :loading="dashboardLoading">
          <BubbleChart :data="bubbleData" :height="400" />
        </PvCard>
      </el-col>
      <el-col :xs="24" :lg="8">
        <PvCard title="高风险场站 TOP" icon="Warning" glow>
          <div class="risk-list">
            <div
              v-for="(item, index) in riskStations"
              :key="item.station_id"
              class="risk-item"
              @click="$router.push(`/stations/${item.station_id}`)"
            >
              <div class="risk-rank" :class="{ top3: index < 3 }">{{ index + 1 }}</div>
              <div class="risk-info">
                <div class="risk-name">{{ item.name }}</div>
                <div class="risk-meta">
                  完成率 {{ (item.completion_rate * 100).toFixed(1) }}% · 损失 ¥{{ item.loss_cny.toFixed(0) }}
                </div>
              </div>
              <PvTag :type="healthTagType(item.health_score)" :label="item.health_score.toFixed(0)" />
            </div>
          </div>
        </PvCard>
      </el-col>
    </el-row>

    <!-- 实时功率 + 健康度 + 告警 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="13">
        <PvCard title="集团实时功率" icon="TrendCharts" glow :loading="dashboardLoading">
          <PowerChart :station-id="1" :height="360" title="实时功率" />
        </PvCard>
      </el-col>
      <el-col :xs="24" :lg="5">
        <PvCard title="系统健康" icon="FirstAidKit" glow :loading="dashboardLoading">
          <GaugeChart :value="overallHealth" title="健康度" unit="分" :height="300" />
        </PvCard>
      </el-col>
      <el-col :xs="24" :lg="6">
        <AlarmPanel :alarms="alarms" />
      </el-col>
    </el-row>

    <!-- 排名 + 容量分布 + 健康度热力图 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="8">
        <PvCard title="电站功率排名" icon="Rank" glow :loading="dashboardLoading">
          <BarChart :data="stationPowerData" unit="kWh" color="#00f0ff" :height="300" />
        </PvCard>
      </el-col>
      <el-col :xs="24" :lg="8">
        <PvCard title="装机容量分布" icon="PieChart" glow :loading="dashboardLoading">
          <DonutChart :data="capacityData" :height="300" />
        </PvCard>
      </el-col>
      <el-col :xs="24" :lg="8">
        <PvCard title="月度健康度热力图" icon="Grid" glow :loading="dashboardLoading">
          <HeatmapChart :data="healthTrend" :height="300" />
        </PvCard>
      </el-col>
    </el-row>

    <!-- 电站列表 -->
    <el-row class="station-row">
      <el-col :span="24">
        <PvCard title="电站运行状态" icon="OfficeBuilding" glow :loading="dashboardLoading" :empty="!overview.length">
          <template #actions>
            <el-button type="primary" size="small" @click="$router.push('/stations')">查看全部</el-button>
          </template>
          <el-table :data="overview" stripe>
            <el-table-column prop="name" label="电站名称" min-width="160" />
            <el-table-column prop="capacity_kw" label="装机容量(kW)" />
            <el-table-column label="健康度" width="110">
              <template #default="{ row }">
                <PvTag :type="healthTagType(row.health_score)" :label="row.health_score.toFixed(0)" />
              </template>
            </el-table-column>
            <el-table-column label="完成率" width="120">
              <template #default="{ row }">
                {{ (row.completion_rate * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column label="今日发电(kWh)" width="140">
              <template #default="{ row }">
                {{ row.daily_energy_kwh.toFixed(0) }}
              </template>
            </el-table-column>
            <el-table-column label="损失金额" width="130">
              <template #default="{ row }">
                ¥{{ row.loss_cny.toFixed(0) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <PvTag :type="row.status === 'active' ? 'running' : 'inactive'" :label="row.status === 'active' ? '运行中' : '停用'" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" type="primary" plain @click="$router.push(`/stations/${row.station_id}`)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </PvCard>
      </el-col>
    </el-row>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Odometer, Cpu, ArrowRight } from '@element-plus/icons-vue'
import { useCopilotStore } from '@/stores/copilot'
import { alarmApi, dashboardApi, metricApi } from '@/services/api'
import DashboardLayout from '@/components/DashboardLayout.vue'
import MetricCard from '@/components/MetricCard.vue'
import PvCard from '@/components/PvCard.vue'
import PvTag from '@/components/PvTag.vue'
import PowerChart from '@/components/PowerChart.vue'
import GaugeChart from '@/components/GaugeChart.vue'
import BarChart from '@/components/BarChart.vue'
import DonutChart from '@/components/DonutChart.vue'
import BubbleChart from '@/components/BubbleChart.vue'
import HeatmapChart from '@/components/HeatmapChart.vue'
import AlarmPanel from '@/components/AlarmPanel.vue'

interface OverviewItem {
  station_id: number
  name: string
  capacity_kw: number
  daily_energy_kwh: number
  completion_rate: number
  loss_kwh: number
  loss_cny: number
  health_score: number
  pr: number
  status: string
}

interface KpiData {
  station_count: number
  online_count: number
  offline_count: number
  total_capacity_kw: number
  total_active_power_kw: number
  total_daily_energy_kwh: number
  alarm_summary: Record<string, number>
  system_health: number
}

const copilotStore = useCopilotStore()

const overview = ref<OverviewItem[]>([])
const riskStations = ref<OverviewItem[]>([])
const healthTrend = ref<{ date: string; health_score: number }[]>([])
const aiInsight = ref('正在分析集团电站运行数据...')
const kpiLoading = ref(true)
const dashboardLoading = ref(true)
const overviewKpi = ref<KpiData>({
  station_count: 0,
  online_count: 0,
  offline_count: 0,
  total_capacity_kw: 0,
  total_active_power_kw: 0,
  total_daily_energy_kwh: 0,
  alarm_summary: { urgent: 0, high: 0, medium: 0, low: 0 },
  system_health: 100,
})
const alarms = ref<any[]>([])

let refreshTimer: ReturnType<typeof setInterval> | null = null

const alarmStatsList = computed(() => [
  { key: 'urgent', label: '紧急', value: overviewKpi.value.alarm_summary.urgent || 0 },
  { key: 'high', label: '重要', value: overviewKpi.value.alarm_summary.high || 0 },
  { key: 'medium', label: '一般', value: overviewKpi.value.alarm_summary.medium || 0 },
  { key: 'low', label: '低', value: overviewKpi.value.alarm_summary.low || 0 },
])

const bubbleData = computed(() => {
  return overview.value.map((s) => ({
    name: s.name,
    value: [s.capacity_kw, s.completion_rate, s.loss_cny, s.health_score] as [number, number, number, number],
  }))
})

const overallHealth = computed(() => Math.round(overviewKpi.value.system_health || 92))

const stationPowerData = computed(() => {
  return overview.value.map((s) => ({ name: s.name, value: Math.round(s.daily_energy_kwh) }))
})

const capacityData = computed(() => {
  return overview.value.map((s) => ({ name: s.name, value: s.capacity_kw || 0 }))
})

const healthTagType = (score: number) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

const formatAlarmTime = (timeStr: string) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 60000)
  if (diff < 1) return '刚刚'
  if (diff < 60) return `${diff}分钟前`
  return `${Math.floor(diff / 60)}小时前`
}

const fetchAlarms = async () => {
  try {
    const data = (await alarmApi.list()) as unknown as any[]
    alarms.value = data.map((a) => ({
      id: a.id,
      title: a.title,
      description: a.description,
      time: formatAlarmTime(a.created_at),
      type: (a.level === 'critical' ? 'danger' : a.level === 'warning' ? 'warning' : 'info') as any,
    }))
  } catch (err) {
    console.error('获取告警失败:', err)
  }
}

const fetchDashboard = async () => {
  dashboardLoading.value = true
  kpiLoading.value = true
  try {
    const [overviewData, riskData, insightData, kpiData] = await Promise.all([
      dashboardApi.stationsOverview(),
      dashboardApi.riskTop(5),
      dashboardApi.insights(),
      dashboardApi.overview(),
    ])
    overview.value = overviewData as unknown as OverviewItem[]
    riskStations.value = riskData as unknown as OverviewItem[]
    aiInsight.value = (insightData as any).insight || aiInsight.value
    overviewKpi.value = kpiData as unknown as KpiData
  } catch (err) {
    console.error('获取总览失败:', err)
  } finally {
    dashboardLoading.value = false
    kpiLoading.value = false
  }
}

const fetchHealthTrend = async () => {
  try {
    // 取第一个电站展示集团示例热力图
    const target = overview.value[0]?.station_id || 1
    const data = await metricApi.getStationHealthTrend(target, 30)
    healthTrend.value = data as unknown as { date: string; health_score: number }[]
  } catch (err) {
    console.error('获取健康趋势失败:', err)
  }
}

onMounted(() => {
  fetchDashboard().then(() => fetchHealthTrend())
  fetchAlarms()
  refreshTimer = setInterval(() => {
    fetchAlarms()
    fetchDashboard()
  }, 10000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.metrics-row {
  margin-bottom: 22px;
}

.insight-row {
  margin-bottom: 22px;
}

.ai-insight-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 22px;
  border-radius: 14px;
  background: linear-gradient(90deg, rgba(0, 240, 255, 0.12), rgba(189, 52, 254, 0.08));
  border: 1px solid rgba(0, 240, 255, 0.18);
  box-shadow: 0 0 24px rgba(0, 240, 255, 0.1);
  cursor: pointer;
  transition: var(--pv-transition);
}

.ai-insight-bar:hover {
  border-color: rgba(0, 240, 255, 0.35);
  box-shadow: 0 0 32px rgba(0, 240, 255, 0.18);
}

.insight-icon {
  color: var(--pv-primary);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { filter: drop-shadow(0 0 4px rgba(0, 240, 255, 0.5)); }
  50% { filter: drop-shadow(0 0 12px rgba(0, 240, 255, 0.9)); }
}

.insight-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  flex: 1;
}

.insight-label {
  font-weight: 800;
  color: var(--pv-primary);
  text-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
}

.insight-text {
  color: var(--pv-text-secondary);
}

.insight-arrow {
  color: var(--pv-text-tertiary);
}

.alarm-stats-row {
  margin-bottom: 22px;
}

.alarm-stat-card {
  padding: 18px;
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(16, 24, 40, 0.9), rgba(8, 12, 22, 0.8));
  border: 1px solid var(--pv-border);
  cursor: pointer;
  transition: var(--pv-transition);
  position: relative;
  overflow: hidden;
}

.alarm-stat-card:hover {
  transform: translateY(-3px);
  border-color: rgba(255, 255, 255, 0.15);
}

.alarm-stat-card::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.alarm-stat-card.urgent::before { background: var(--pv-danger); box-shadow: 0 0 12px var(--pv-danger); }
.alarm-stat-card.high::before { background: var(--pv-warning); box-shadow: 0 0 12px var(--pv-warning); }
.alarm-stat-card.medium::before { background: var(--pv-info); box-shadow: 0 0 12px var(--pv-info); }
.alarm-stat-card.low::before { background: var(--pv-success); box-shadow: 0 0 12px var(--pv-success); }

.alarm-stat-value {
  font-size: 28px;
  font-weight: 900;
  font-family: var(--pv-font-display);
  color: var(--pv-text-primary);
  margin-bottom: 6px;
}

.alarm-stat-label {
  font-size: 13px;
  color: var(--pv-text-secondary);
}

.chart-row {
  margin-bottom: 22px;
}

.risk-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--pv-border);
  cursor: pointer;
  transition: all 0.2s;
}

.risk-item:hover {
  background: rgba(0, 240, 255, 0.06);
  border-color: rgba(0, 240, 255, 0.25);
}

.risk-rank {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  color: var(--pv-text-tertiary);
  background: rgba(255, 255, 255, 0.05);
}

.risk-rank.top3 {
  color: #fff;
  background: linear-gradient(135deg, #ff2a6d, #ff5c8a);
  box-shadow: 0 0 12px rgba(255, 42, 109, 0.4);
}

.risk-info {
  flex: 1;
}

.risk-name {
  font-weight: 700;
  color: var(--pv-text-primary);
  margin-bottom: 4px;
}

.risk-meta {
  font-size: 12px;
  color: var(--pv-text-tertiary);
}

.station-row {
  margin-bottom: 22px;
}
</style>
