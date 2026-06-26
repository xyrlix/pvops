<template>
  <DashboardLayout>
    <template #title>
      <span class="pv-page-title">运营总览</span>
    </template>
    <template #subtitle>
      GROUP COMMAND · {{ currentTimeLabel }}
    </template>

    <!-- AI 洞察 -->
    <div class="ai-insight-bar" @click="copilotStore.open({ type: 'overview' })">
      <el-icon class="insight-icon" :size="20"><Cpu /></el-icon>
      <div class="insight-content">
        <span class="insight-label">AI INSIGHT</span>
        <span class="insight-text">{{ aiInsight }}</span>
      </div>
      <el-icon class="insight-arrow"><ArrowRight /></el-icon>
    </div>

    <!-- 信号条 -->
    <div class="pv-strip" style="margin-bottom: 22px;">
      <span><strong class="pv-text-glow">{{ overviewKpi.online_count }}</strong> 座在线</span>
      <span>·</span>
      <span><strong>{{ overviewKpi.offline_count }}</strong> 离线</span>
      <span>·</span>
      <span>采集频率 <strong class="pv-number">5s</strong></span>
      <span>·</span>
      <span>数据延迟 <strong class="pv-number">&lt; 1.5s</strong></span>
    </div>

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
import { Cpu, ArrowRight } from '@element-plus/icons-vue'
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

const currentTimeLabel = computed(() => {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
})

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
  padding: 14px 20px;
  border-radius: 12px;
  background: linear-gradient(90deg, rgba(34, 211, 238, 0.1), rgba(129, 140, 248, 0.06));
  border: 1px solid var(--pv-border-strong);
  cursor: pointer;
  transition: var(--pv-transition);
  margin-bottom: 22px;
}

.ai-insight-bar:hover {
  border-color: var(--pv-primary);
  box-shadow: var(--pv-glow-primary);
}

.insight-icon {
  color: var(--pv-primary);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { filter: drop-shadow(0 0 4px rgba(34, 211, 238, 0.5)); }
  50% { filter: drop-shadow(0 0 12px rgba(34, 211, 238, 0.9)); }
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
  font-family: var(--pv-font-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  color: var(--pv-primary);
  padding: 3px 8px;
  border: 1px solid rgba(34, 211, 238, 0.3);
  border-radius: 4px;
  background: rgba(34, 211, 238, 0.08);
}

.insight-text {
  color: var(--pv-text-secondary);
  font-size: 13px;
}

.insight-arrow {
  color: var(--pv-text-tertiary);
}

.alarm-stats-row {
  margin-bottom: 22px;
}

.alarm-stat-card {
  padding: 16px 18px;
  border-radius: 12px;
  background: var(--pv-surface);
  border: 1px solid var(--pv-border);
  cursor: pointer;
  transition: var(--pv-transition);
  position: relative;
  overflow: hidden;
}

.alarm-stat-card:hover {
  transform: translateY(-2px);
  border-color: var(--pv-border-strong);
}

.alarm-stat-card::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
}

.alarm-stat-card.urgent::before { background: var(--pv-danger); box-shadow: 0 0 12px var(--pv-danger); }
.alarm-stat-card.high::before { background: var(--pv-warning); box-shadow: 0 0 12px var(--pv-warning); }
.alarm-stat-card.medium::before { background: var(--pv-info); box-shadow: 0 0 12px var(--pv-info); }
.alarm-stat-card.low::before { background: var(--pv-success); box-shadow: 0 0 12px var(--pv-success); }

.alarm-stat-value {
  font-family: var(--pv-font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 28px;
  font-weight: 600;
  color: var(--pv-text-primary);
  margin-bottom: 4px;
  line-height: 1.1;
}

.alarm-stat-label {
  font-size: 11px;
  font-weight: 600;
  font-family: var(--pv-font-mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--pv-text-tertiary);
}

.chart-row {
  margin-bottom: 22px;
}

.risk-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--pv-stripe);
  border: 1px solid var(--pv-border);
  cursor: pointer;
  transition: var(--pv-transition);
}

.risk-item:hover {
  background: rgba(34, 211, 238, 0.06);
  border-color: var(--pv-border-strong);
}

.risk-rank {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-family: var(--pv-font-mono);
  font-size: 12px;
  color: var(--pv-text-tertiary);
  background: var(--pv-stripe);
  flex-shrink: 0;
}

.risk-rank.top3 {
  color: #fff;
  background: linear-gradient(135deg, var(--pv-danger), #fb7185);
  box-shadow: 0 0 10px rgba(244, 63, 94, 0.4);
}

.risk-info {
  flex: 1;
  min-width: 0;
}

.risk-name {
  font-weight: 600;
  color: var(--pv-text-primary);
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.risk-meta {
  font-size: 11px;
  font-family: var(--pv-font-mono);
  color: var(--pv-text-tertiary);
  letter-spacing: 0.02em;
}

.station-row {
  margin-bottom: 22px;
}
</style>
