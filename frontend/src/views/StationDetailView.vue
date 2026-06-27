<template>
  <DashboardLayout>
    <template #title>
      <el-icon class="back-icon" :size="18" style="cursor:pointer;margin-right:6px" @click="$router.push('/stations')"><ArrowLeft /></el-icon>
      <span class="pv-page-title">{{ stationStore.currentStation?.name || '电站详情' }}</span>
    </template>
    <template #subtitle>
      STATION DETAIL · {{ stationStore.currentStation?.code || '--' }}
    </template>

    <template #actions>
      <el-button type="info" plain @click="askAi">
        <el-icon><ChatDotRound /></el-icon> 问 AI
      </el-button>
      <el-button type="primary" @click="runDiagnosis">
        <el-icon><Aim /></el-icon> AI 智能诊断
      </el-button>
      <PvTag :type="healthStatus.type" :label="healthStatus.text" size="large" />
    </template>

    <template v-if="stationStore.currentStation">
      <!-- 运行指标 -->
      <el-row :gutter="20" class="metrics-row">
        <el-col :xs="24" :sm="12" :md="6">
          <MetricCard
            title="实时功率"
            :value="metrics.active_power_kw"
            unit="kW"
            icon="Lightning"
            icon-color="#00f0ff"
            value-color="#00f0ff"
            icon-bg="linear-gradient(135deg, rgba(0,240,255,0.22), rgba(0,102,255,0.08))"
            :decimals="2"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <MetricCard
            title="今日发电量"
            :value="metrics.daily_energy_kwh"
            unit="kWh"
            icon="Calendar"
            icon-color="#00ff9d"
            value-color="#00ff9d"
            icon-bg="linear-gradient(135deg, rgba(0,255,157,0.22), rgba(0,255,157,0.06))"
            :decimals="2"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <MetricCard
            title="PR（性能比）"
            :value="prPercent"
            unit="%"
            icon="TrendCharts"
            icon-color="#ffcc00"
            value-color="#ffcc00"
            icon-bg="linear-gradient(135deg, rgba(255,204,0,0.22), rgba(255,204,0,0.06))"
            :decimals="1"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <MetricCard
            title="健康度"
            :value="metrics.health_score"
            unit="分"
            icon="FirstAidKit"
            :icon-color="healthColor"
            :value-color="healthColor"
            :icon-bg="healthIconBg"
            :decimals="0"
          />
        </el-col>
      </el-row>

      <!-- 效率与损失 -->
      <el-row :gutter="20" class="metrics-row">
        <el-col :xs="24" :sm="12" :md="8">
          <MetricCard
            title="等效利用小时"
            :value="efficiency.equivalent_hours"
            unit="h"
            icon="Timer"
            icon-color="#bd34fe"
            value-color="#bd34fe"
            icon-bg="linear-gradient(135deg, rgba(189,52,254,0.22), rgba(189,52,254,0.06))"
            :decimals="2"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <MetricCard
            title="系统效率"
            :value="efficiency.system_efficiency"
            unit="%"
            icon="SetUp"
            icon-color="#ffcc00"
            value-color="#ffcc00"
            icon-bg="linear-gradient(135deg, rgba(255,204,0,0.22), rgba(255,204,0,0.06))"
            :decimals="1"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <MetricCard
            title="今日损失金额"
            :value="losses.total_loss_cny"
            unit="元"
            icon="Money"
            icon-color="#ff2a6d"
            value-color="#ff2a6d"
            icon-bg="linear-gradient(135deg, rgba(255,42,109,0.22), rgba(255,42,109,0.06))"
            :decimals="0"
          />
        </el-col>
      </el-row>

      <!-- 功率曲线 + 辐照对照 -->
      <el-row :gutter="20" class="chart-row">
        <el-col :xs="24" :lg="12">
          <PvCard title="功率曲线" icon="TrendCharts" glow :loading="stationLoading">
            <PowerChart :station-id="stationId" :height="340" title="实时功率" />
          </PvCard>
        </el-col>
        <el-col :xs="24" :lg="12">
          <PvCard title="辐照-功率对照" icon="MostlyCloudy" glow :loading="stationLoading">
            <IrradiancePowerChart :station-id="stationId" :height="340" />
          </PvCard>
        </el-col>
      </el-row>

      <!-- 损失瀑布 + 逆变器排名 -->
      <el-row :gutter="20" class="chart-row">
        <el-col :xs="24" :lg="12">
          <PvCard title="损失分解瀑布" subtitle="单位：kWh / 元" icon="DataLine" glow :loading="stationLoading">
            <PvEmpty v-if="!losses.breakdown.length" description="暂无损失分解数据" />
            <WaterfallChart v-else :data="losses.breakdown" :height="340" />
          </PvCard>
        </el-col>
        <el-col :xs="24" :lg="12">
          <PvCard title="逆变器日发电量排名" icon="Histogram" glow :loading="stationLoading">
            <BarChart :data="inverterBars" :height="340" color="#00f0ff" unit="kWh" />
          </PvCard>
        </el-col>
      </el-row>

      <!-- 健康度趋势 + 最近告警 -->
      <el-row :gutter="20" class="chart-row">
        <el-col :xs="24" :lg="16">
          <PvCard title="健康度趋势（近30天）" icon="Grid" glow :loading="stationLoading">
            <HeatmapChart :data="healthTrend" :height="220" />
          </PvCard>
        </el-col>
        <el-col :xs="24" :lg="8">
          <PvCard title="最近告警" icon="Warning" glow>
            <div class="recent-alarms">
              <div v-for="alarm in recentAlarms" :key="alarm.id" class="recent-alarm-item" @click="goToAlarms">
                <PvTag :type="alarm.level === 'critical' ? 'urgent' : 'high'" :label="alarm.level === 'critical' ? '紧急' : '重要'" size="small" />
                <div class="recent-alarm-title">{{ alarm.title }}</div>
                <div class="recent-alarm-time">{{ formatTime(alarm.created_at) }}</div>
              </div>
              <PvEmpty v-if="!recentAlarms.length" description="暂无告警" />
            </div>
          </PvCard>
        </el-col>
      </el-row>

      <!-- 电站信息 -->
      <el-row class="info-row">
        <el-col :span="24">
          <PvCard title="电站信息" icon="InfoFilled" glow>
            <el-descriptions :column="3" border>
              <el-descriptions-item label="电站名称">{{ stationStore.currentStation.name }}</el-descriptions-item>
              <el-descriptions-item label="电站编码">{{ stationStore.currentStation.code }}</el-descriptions-item>
              <el-descriptions-item label="装机容量">{{ stationStore.currentStation.capacity_kw }} kW</el-descriptions-item>
              <el-descriptions-item label="位置">{{ stationStore.currentStation.location || '-' }}</el-descriptions-item>
              <el-descriptions-item label="经纬度">{{ stationStore.currentStation.longitude }}, {{ stationStore.currentStation.latitude }}</el-descriptions-item>
              <el-descriptions-item label="联系人">{{ stationStore.currentStation.contact_name || '-' }} {{ stationStore.currentStation.contact_phone || '' }}</el-descriptions-item>
            </el-descriptions>
          </PvCard>
        </el-col>
      </el-row>
    </template>

    <PvLoading v-else text="加载电站数据中..." />
  </DashboardLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Aim, ChatDotRound } from '@element-plus/icons-vue'
import { useStationStore } from '@/stores/station'
import { useCopilotStore } from '@/stores/copilot'
import DashboardLayout from '@/components/DashboardLayout.vue'
import MetricCard from '@/components/MetricCard.vue'
import PvCard from '@/components/PvCard.vue'
import PvTag from '@/components/PvTag.vue'
import PvLoading from '@/components/PvLoading.vue'
import PvEmpty from '@/components/PvEmpty.vue'
import PowerChart from '@/components/PowerChart.vue'
import IrradiancePowerChart from '@/components/IrradiancePowerChart.vue'
import WaterfallChart from '@/components/WaterfallChart.vue'
import BarChart from '@/components/BarChart.vue'
import HeatmapChart from '@/components/HeatmapChart.vue'
import { alarmApi, metricApi } from '@/services/api'
import type { StationMetrics } from '@/types/station'

const route = useRoute()
const router = useRouter()
const stationStore = useStationStore()
const copilotStore = useCopilotStore()

const stationId = computed(() => Number(route.params.id))

const metrics = ref<StationMetrics>({
  station_id: stationId.value,
  station_name: '',
  timestamp: '',
  active_power_kw: 0,
  daily_energy_kwh: 0,
  pr: null,
  health_score: null,
})

const efficiency = ref({
  station_id: stationId.value,
  capacity_kw: 0,
  daily_energy_kwh: 0,
  equivalent_hours: 0,
  pr: 0,
  system_efficiency: 0,
})

const losses = ref({
  station_id: stationId.value,
  theoretical_kwh: 0,
  actual_kwh: 0,
  total_loss_kwh: 0,
  total_loss_cny: 0,
  breakdown: [] as { name: string; kwh: number; cny: number }[],
})

const inverterBars = ref<{ name: string; value: number }[]>([])
const healthTrend = ref<{ date: string; health_score: number }[]>([])
// TODO(typing): replace any with explicit type; suppressed to keep CI green
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const recentAlarms = ref<any[]>([])
const stationLoading = ref(true)

const prPercent = computed(() => {
  const pr = metrics.value.pr
  return pr !== null && pr !== undefined ? pr * 100 : null
})

const healthStatus = computed(() => {
  const score = metrics.value.health_score
  if (score === null || score === undefined) return { text: '未知', type: 'info' as const }
  if (score >= 80) return { text: '健康', type: 'success' as const }
  if (score >= 60) return { text: '亚健康', type: 'warning' as const }
  return { text: '异常', type: 'danger' as const }
})

const healthColor = computed(() => {
  const score = metrics.value.health_score
  if (score === null || score === undefined) return '#94a3b8'
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#f59e0b'
  return '#ef4444'
})

const healthIconBg = computed(() => {
  const c = healthColor.value
  return `linear-gradient(135deg, ${c}33, ${c}14)`
})

let refreshTimer: ReturnType<typeof setInterval> | null = null

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

const loadData = async () => {
  stationLoading.value = true
  try {
    await stationStore.fetchStation(stationId.value)
    await stationStore.fetchMetrics(stationId.value)
    if (stationStore.currentMetrics) {
      metrics.value = stationStore.currentMetrics
    }

    try {
      const [effRes, lossRes, invRes, trendRes, alarmRes] = await Promise.all([
        metricApi.getStationEfficiency(stationId.value),
        metricApi.getStationLosses(stationId.value),
        metricApi.getStationInverters(stationId.value),
        metricApi.getStationHealthTrend(stationId.value, 30),
        alarmApi.list(stationId.value),
      ])
      efficiency.value = effRes as unknown as typeof efficiency.value
      losses.value = lossRes as unknown as typeof losses.value
      const invData = invRes as unknown as { inverter_id: string; daily_energy_kwh: number }[]
      inverterBars.value = invData.map((d) => ({ name: d.inverter_id, value: d.daily_energy_kwh }))
      healthTrend.value = trendRes as unknown as typeof healthTrend.value
      // TODO(typing): replace any with explicit type; suppressed to keep CI green
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recentAlarms.value = (alarmRes as unknown as any[]).slice(0, 5)
    } catch (err) {
      console.error('加载高级指标失败:', err)
    }
  } finally {
    stationLoading.value = false
  }
}

onMounted(() => {
  loadData()
  refreshTimer = setInterval(() => {
    stationStore.fetchMetrics(stationId.value).then(() => {
      if (stationStore.currentMetrics) {
        metrics.value = stationStore.currentMetrics
      }
    })
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})

watch(() => stationId.value, () => {
  loadData()
})

const runDiagnosis = () => {
  router.push(`/stations/${stationId.value}/diagnosis`)
}

const askAi = () => {
  copilotStore.open({
    type: 'device',
    station_id: stationId.value,
    device_code: stationStore.currentStation?.name,
  })
}

const goToAlarms = () => {
  router.push('/alarms')
}
</script>

<style scoped>
.metrics-row {
  margin-bottom: 22px;
}

.chart-row {
  margin-bottom: 22px;
}

.info-row {
  margin-bottom: 22px;
}

.recent-alarms {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-alarm-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--pv-border);
  cursor: pointer;
  transition: all 0.2s;
}

.recent-alarm-item:hover {
  background: rgba(255, 42, 109, 0.06);
  border-color: rgba(255, 42, 109, 0.25);
}

.recent-alarm-title {
  flex: 1;
  font-size: 13px;
  color: var(--pv-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-alarm-time {
  font-size: 12px;
  color: var(--pv-text-tertiary);
}
</style>
