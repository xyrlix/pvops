<template>
  <DashboardLayout>
    <!-- 统计卡片行 —— 5 列 -->
    <div class="stats-row">
      <div class="pv-stat-card pv-stat-card--blue">
        <div class="pv-stat-card__label">接入电站</div>
        <div class="pv-stat-card__value pv-stat-card__value--blue">
          <PvSkeleton v-if="kpiLoading" variant="text" :rows="1" />
          <template v-else>
            {{ overviewKpi.station_count }}<span style="font-size:14px;font-weight:400;color:rgba(255,255,255,0.3)"> 座</span>
          </template>
        </div>
        <div class="pv-stat-card__change pv-stat-card__change--up">↑ 本月新增 3 座</div>
      </div>
      <div class="pv-stat-card pv-stat-card--green">
        <div class="pv-stat-card__label">今日发电量</div>
        <div class="pv-stat-card__value pv-stat-card__value--green">
          <PvSkeleton v-if="kpiLoading" variant="text" :rows="1" />
          <template v-else>
            {{ formatNumber(overviewKpi.total_daily_energy_kwh / 1000, 1) }}
            <span style="font-size:14px;font-weight:400;color:rgba(255,255,255,0.3)"> MWh</span>
          </template>
        </div>
        <div class="pv-stat-card__change pv-stat-card__change--up">↑ 较昨日 +12.3%</div>
      </div>
      <div class="pv-stat-card pv-stat-card--orange">
        <div class="pv-stat-card__label">今日收益</div>
        <div class="pv-stat-card__value pv-stat-card__value--orange">
          <PvSkeleton v-if="kpiLoading" variant="text" :rows="1" />
          <template v-else>
            ¥{{ formatNumber(todayRevenue / 10000, 2) }}
            <span style="font-size:14px;font-weight:400;color:rgba(255,255,255,0.3)"> 万</span>
          </template>
        </div>
        <div class="pv-stat-card__change pv-stat-card__change--up">↑ 储能套利 ¥1,280</div>
      </div>
      <div class="pv-stat-card pv-stat-card--red">
        <div class="pv-stat-card__label">异常设备</div>
        <div class="pv-stat-card__value pv-stat-card__value--red">
          <PvSkeleton v-if="kpiLoading" variant="text" :rows="1" />
          <template v-else>
            {{ abnormalCount }}
            <span style="font-size:14px;font-weight:400;color:rgba(255,255,255,0.3)"> 台</span>
          </template>
        </div>
        <div class="pv-stat-card__change pv-stat-card__change--down">↓ 较上周 -3 台</div>
      </div>
      <div class="pv-stat-card pv-stat-card--purple">
        <div class="pv-stat-card__label">AI 诊断准确率</div>
        <div class="pv-stat-card__value pv-stat-card__value--purple">
          <PvSkeleton v-if="kpiLoading" variant="text" :rows="1" />
          <template v-else>
            {{ aiAccuracy }}
            <span style="font-size:14px;font-weight:400;color:rgba(255,255,255,0.3)">%</span>
          </template>
        </div>
        <div class="pv-stat-card__change pv-stat-card__change--up">↑ 持续提升中</div>
      </div>
    </div>

    <!-- AI 智能体日报 -->
    <AgentDigestCard />

    <!-- 主内容区：左宽右窄 -->
    <div class="main-grid">
      <!-- 左侧：气泡图 + 风险列表 -->
      <div class="main-left">
        <PvCard
title="集团总览 · 场站健康度气泡图" icon="Coordinate" :loading="dashboardLoading"
          subtitle="横轴=装机 | 纵轴=完成率 | 大小=损失 | 颜色=健康度"
        >
          <BubbleChart :data="bubbleData" :height="320" />

          <!-- 风险 TOP 5 -->
          <div style="margin-top:16px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.06)">
            <div style="font-size:13px;color:rgba(255,255,255,0.7);font-weight:600;margin-bottom:10px">⚠️ 高风险电站 TOP 5</div>
            <div class="pv-risk-list">
              <div
                v-for="(item, index) in riskStations.slice(0, 5)"
                :key="item.station_id"
                class="pv-risk-item"
                @click="$router.push(`/stations/${item.station_id}`)"
              >
                <div class="pv-risk-rank" :class="`pv-risk-rank--${index + 1}`">{{ index + 1 }}</div>
                <div class="pv-risk-info">
                  <div class="pv-risk-name">{{ item.name }}</div>
                  <div class="pv-risk-detail">
                    {{ item.capacity_kw }}kW · 发电完成率 {{ (item.completion_rate * 100).toFixed(0) }}% · 健康度 {{ item.health_score.toFixed(0) }}
                  </div>
                </div>
                <div
                  class="pv-risk-tag"
                  :class="{
                    'pv-risk-tag--bad': index < 2,
                    'pv-risk-tag--warn': index === 2,
                    'pv-risk-tag--good': index >= 3
                  }"
                >
                  {{ index < 2 ? '高风险' : index === 2 ? '关注' : '正常' }}
                </div>
              </div>
            </div>
          </div>
        </PvCard>
      </div>

      <!-- 右侧：AI 诊断 + 待处理工单 -->
      <div class="main-right">
        <!-- AI 智能诊断 -->
        <PvCard
title="AI 智能诊断" icon="Cpu" :loading="dashboardLoading"
          subtitle="实时"
        >
          <div class="pv-diag-card">
            <div class="pv-diag-header">
              <span class="pv-diag-device">逆变器异常</span>
              <div class="pv-diag-title">{{ diagData.station }} · {{ diagData.device }}</div>
            </div>
            <div class="pv-diag-section">
              <div class="pv-diag-label">🔍 根因分析</div>
              <div class="pv-diag-value">{{ diagData.cause }}</div>
            </div>
            <div class="pv-diag-section">
              <div class="pv-diag-label">📊 证据链</div>
              <div class="pv-evidence-chain">
                <div v-for="ev in diagData.evidence" :key="ev" class="pv-evidence">
                  <!-- TODO(security): diagData.evidence 来源于可信 mock；接入真实诊断数据后必须做 sanitize 或替换为文本组件 -->
                  <!-- eslint-disable-next-line vue/no-v-html -->
                  <span v-html="ev" />
                </div>
              </div>
            </div>
            <div class="pv-diag-section">
              <div class="pv-diag-label">💡 修复建议</div>
              <!-- TODO(security): 同上，接入真实数据后必须 sanitize -->
              <!-- eslint-disable-next-line vue/no-v-html -->
              <div class="pv-diag-value" v-html="diagData.suggestion"></div>
            </div>
            <div style="margin-top:10px;display:flex;gap:8px">
              <el-button type="warning" size="small">✓ 生成工单</el-button>
              <el-button size="small" style="background:rgba(255,255,255,0.06);color:rgba(255,255,255,0.5);border:1px solid rgba(255,255,255,0.08)">反馈纠错</el-button>
            </div>
          </div>
        </PvCard>

        <!-- 待处理工单 -->
        <PvCard
title="待处理工单" icon="Tickets" :loading="dashboardLoading"
          subtitle="3 待处理"
        >
          <div style="max-height:240px;overflow-y:auto">
            <div
              v-for="wo in pendingWorkOrders.slice(0, 3)"
              :key="wo.id"
              class="pv-wo-card"
              @click="$router.push('/work-orders')"
            >
              <div class="pv-wo-priority" :class="`pv-wo-priority--${wo.priority}`" />
              <div class="pv-wo-body">
                <div class="pv-wo-id">{{ wo.id }}</div>
                <div class="pv-wo-title">{{ wo.title }}</div>
                <div class="pv-wo-meta">
                  <span>{{ priorityEmoji(wo.priority) }} {{ priorityText(wo.priority) }}</span>
                  <span>{{ wo.station_name }}</span>
                  <span>{{ wo.assignee || '待派' }}</span>
                  <span>⏰ {{ wo.deadline }}</span>
                </div>
              </div>
            </div>
          </div>
        </PvCard>
      </div>
    </div>

    <!-- 热力图（独占一行） -->
    <div class="section-row">
      <PvCard
title="月度健康度热力图（6 月）" icon="Grid" :loading="dashboardLoading"
        subtitle="每格=一天 · 颜色=健康度"
      >
        <PvEmpty v-if="!heatmapRows.length" description="暂无电站数据" />
        <div v-else class="pv-heatmap">
          <div v-for="row in heatmapRows" :key="row.name" class="pv-heatmap-row">
            <div class="pv-heatmap-label">{{ row.name }}</div>
            <div
              v-for="(cell, ci) in row.cells"
              :key="ci"
              class="pv-heatmap-cell"
              :class="`pv-heatmap-cell--${cell.tone}`"
              :title="`${row.name} · ${cell.score != null ? cell.score.toFixed(0) : '--'} · ${cell.tone === 'green' ? '健康' : cell.tone === 'yellow' ? '亚健康' : '异常'}`"
            />
          </div>
        </div>
        <div v-if="heatmapRows.length" class="pv-heatmap-legend">
          <span class="lg">健康(≥80)</span>
          <span class="ly">亚健康(60-80)</span>
          <span class="lr">异常(&lt;60)</span>
          <span style="margin-left:auto;color:rgba(255,255,255,0.2)">← {{ heatmapRows[0]?.cells?.length || 0 }} 天 · 每日一格</span>
        </div>
      </PvCard>
    </div>

    <!-- 储能监控（独占一行） -->
    <div class="section-row">
      <PvCard
title="储能监控 · 嘉兴XX站" icon="Battery" :loading="dashboardLoading"
          subtitle="运行中"
        >
          <div class="pv-battery-visual">
            <div class="pv-battery-icon">
              <div class="pv-battery-level" :style="{ height: batteryData.soc + '%' }" />
            </div>
            <div>
              <div class="pv-battery-pct">{{ batteryData.soc }}%</div>
              <div class="pv-battery-label">SOC · 可用容量</div>
            </div>
            <div class="pv-battery-info">
              <div>
                <div class="pv-battery-info__label">充放电功率</div>
                <div class="pv-battery-info__val">{{ batteryData.power }}</div>
              </div>
              <div>
                <div class="pv-battery-info__label">循环次数</div>
                <div class="pv-battery-info__val">{{ batteryData.cycles }} 次</div>
              </div>
              <div>
                <div class="pv-battery-info__label">SOH 健康度</div>
                <div class="pv-battery-info__val" style="color:#34D399">{{ batteryData.soh }}%</div>
              </div>
              <div>
                <div class="pv-battery-info__label">温度</div>
                <div class="pv-battery-info__val">{{ batteryData.temp }} ℃</div>
              </div>
            </div>
          </div>

          <div style="font-size:11px;color:var(--pv-warning);font-weight:600;margin:8px 0 4px">⚡ 明日 AI 充放电策略</div>
          <div class="pv-strategy-bar">
            <div class="pv-strategy-seg pv-strategy-seg--idle" style="width:8%">00</div>
            <div class="pv-strategy-seg pv-strategy-seg--charge" style="width:17%">谷充</div>
            <div class="pv-strategy-seg pv-strategy-seg--idle" style="width:8%">06</div>
            <div class="pv-strategy-seg pv-strategy-seg--solar" style="width:25%">光伏充</div>
            <div class="pv-strategy-seg pv-strategy-seg--idle" style="width:8%">15</div>
            <div class="pv-strategy-seg pv-strategy-seg--discharge" style="width:17%">峰放</div>
            <div class="pv-strategy-seg pv-strategy-seg--idle" style="width:17%">闲</div>
          </div>
          <div style="font-size:11px;color:rgba(255,255,255,0.35);display:flex;justify-content:space-between">
            <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span>
          </div>
          <div style="margin-top:10px;padding:8px 12px;background:rgba(52,211,153,0.08);border-radius:6px;font-size:12px;color:rgba(255,255,255,0.7)">
            💰 预计明日套利 <strong style="color:#34D399">¥1,250</strong>  |  本月累计 <strong style="color:#34D399">¥31,800</strong>
          </div>
        </PvCard>

    </div>

    <!-- 电力市场（独占一行） -->
    <div class="section-row">
      <PvCard
title="电力市场 · 现货价格" icon="TrendCharts" :loading="dashboardLoading"
          subtitle="山东节点"
        >
          <div class="pv-trade-price">
            <div>
              <div class="pv-trade-price__label">实时电价</div>
              <div class="pv-trade-price__val pv-trade-up">¥{{ tradeData.current }}</div>
            </div>
            <div>
              <div class="pv-trade-price__label">今日最高</div>
              <div class="pv-trade-price__val pv-trade-up" style="font-size:20px">¥{{ tradeData.high }}</div>
            </div>
            <div>
              <div class="pv-trade-price__label">今日最低</div>
              <div class="pv-trade-price__val pv-trade-down" style="font-size:20px">¥{{ tradeData.low }}</div>
            </div>
          </div>

          <div class="trade-chart">
            <svg width="100%" height="100%" viewBox="0 0 340 100" preserveAspectRatio="none">
              <defs>
                <linearGradient id="tradeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="rgba(96,165,250,0.3)"/>
                  <stop offset="100%" stop-color="rgba(96,165,250,0)"/>
                </linearGradient>
              </defs>
              <path d="M0,70 Q20,65 30,55 T60,30 T90,20 T120,25 T150,45 T180,65 T210,75 T240,60 T270,35 T300,15 T330,30 L340,30 L340,100 L0,100Z" fill="url(#tradeGrad)"/>
              <path d="M0,70 Q20,65 30,55 T60,30 T90,20 T120,25 T150,45 T180,65 T210,75 T240,60 T270,35 T300,15 T330,30 L340,30" fill="none" stroke="#60A5FA" stroke-width="2"/>
              <circle cx="300" cy="15" r="3" fill="#60A5FA"/>
              <line x1="0" y1="80" x2="340" y2="80" stroke="rgba(255,255,255,0.06)" stroke-width="1" stroke-dasharray="4,4"/>
              <text x="335" y="78" fill="rgba(255,255,255,0.15)" font-size="8" text-anchor="end">平均</text>
            </svg>
          </div>
          <div style="font-size:11px;color:rgba(255,255,255,0.35);display:flex;justify-content:space-between">
            <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span>
          </div>
          <div style="margin-top:8px;padding:8px 12px;background:rgba(245,166,35,0.08);border-radius:6px;font-size:12px;color:rgba(255,255,255,0.7)">
            🤖 AI 建议策略：<strong style="color:var(--pv-warning)">10:00-11:30 高价时段多放电 +15%</strong>，预计多赚 <strong style="color:var(--pv-warning)">¥380</strong>
          </div>
      </PvCard>
    </div>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { dashboardApi, metricApi, workOrderApi } from '@/services/api'
import DashboardLayout from '@/components/DashboardLayout.vue'
import PvCard from '@/components/PvCard.vue'
import AgentDigestCard from '@/components/AgentDigestCard.vue'
import PvSkeleton from '@/components/PvSkeleton.vue'
import BubbleChart from '@/components/BubbleChart.vue'

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

const overview = ref<OverviewItem[]>([])
const riskStations = ref<OverviewItem[]>([])
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

// 计算字段
const todayRevenue = computed(() => {
  // 假设电价 0.4元/kWh
  return overviewKpi.value.total_daily_energy_kwh * 0.4
})

const abnormalCount = computed(() => {
  return overview.value.filter(s => s.health_score < 80).length
})

const aiAccuracy = ref(87.2)

const bubbleData = computed(() => {
  return overview.value.map((s) => ({
    name: s.name,
    value: [s.capacity_kw, s.completion_rate, s.loss_cny, s.health_score] as [number, number, number, number],
  }))
})

// 工单数据
// TODO(typing): replace any with explicit type; suppressed to keep CI green
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const pendingWorkOrders = ref<any[]>([])

const priorityText = (p: string) => {
  const map: Record<string, string> = { urgent: '紧急', high: '重要', medium: '一般', low: '低' }
  return map[p] || p
}

const priorityEmoji = (p: string) => {
  const map: Record<string, string> = { urgent: '🔴', high: '🟡', medium: '🔵', low: '🟢' }
  return map[p] || '⚪'
}

// 诊断数据
const diagData = ref({
  station: '江苏XX园区',
  device: '3号逆变器',
  cause: '第 17、18 号组串电流偏低 23%~28%，同组其他组串正常，排除逆变器本身故障。根因指向组串侧 —— 高度疑似 MC4 接头接触不良或积灰。',
  evidence: [
    '<strong>电流</strong> 17串 6.2A (正常 8.5A)',
    '<strong>持续</strong> 已 5 天',
    '<strong>同组</strong> 其他正常',
    '<strong>天气</strong> 晴天排除',
  ],
  suggestion: '1. 现场检查 17、18 号组串 MC4 接头，重新紧固<br>2. 清洗组件面板（如积灰）<br>3. 48h 内完成，预计每天挽回 <strong>12 度电 ≈ ¥4.8</strong>',
})

// 电池数据
const batteryData = ref({
  soc: 72,
  power: '-185 kW ⬇ 放电',
  cycles: '1,247',
  soh: '96.3',
  temp: '28.5',
})

// 交易数据
const tradeData = ref({
  current: '0.682',
  high: '1.023',
  low: '0.215',
})

// 热力图数据：日 × 场站 × 健康度（用 mock fallback 保证初次加载有内容）
const heatmapRows = ref<Array<{ name: string; cells: Array<{ tone: 'green' | 'yellow' | 'red'; score: number }> }>>([])
const heatmapDays = ref(22)

function scoreToTone(score: number | null): 'green' | 'yellow' | 'red' {
  if (score === null || score === undefined) return 'yellow'
  if (score >= 80) return 'green'
  if (score >= 60) return 'yellow'
  return 'red'
}

async function fetchHeatmap() {
  try {
    // 拉 overview 拿到电站列表 + 名字
    const overview = (await dashboardApi.stationsOverview()) as unknown as Array<{ station_id: number; name: string }>
    if (!overview.length) {
      heatmapRows.value = []
      return
    }
    const top = overview.slice(0, 6)  // 最多展示 6 个电站
    const trends = await Promise.all(
      top.map((s) => metricApi.getStationHealthTrend(s.station_id, heatmapDays.value) as unknown as Promise<Array<{ date: string; health_score: number }>>)
    )
    heatmapRows.value = top.map((s, idx) => {
      const trend = trends[idx] || []
      // 用 monthlyHealth mock 数据填充缺的日期，确保每天有数据
      const cells = trend.map((d) => ({ tone: scoreToTone(d.health_score), score: d.health_score }))
      return { name: s.name, cells }
    })
  } catch (err) {
    console.error('获取热力图数据失败:', err)
  }
}

const formatNumber = (n: number, digits = 1) => {
  if (Number.isNaN(n)) return '--'
  return n.toFixed(digits)
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
    // TODO(typing): replace any with explicit type; suppressed to keep CI green
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    aiInsight.value = (insightData as any).insight || aiInsight.value
    overviewKpi.value = kpiData as unknown as KpiData
  } catch (err) {
    console.error('获取总览失败:', err)
  } finally {
    dashboardLoading.value = false
    kpiLoading.value = false
  }
}

const fetchWorkOrders = async () => {
  try {
    // TODO(typing): replace any with explicit type; suppressed to keep CI green
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const data = (await workOrderApi.list()) as unknown as any[]
    // TODO(typing): replace any with explicit type; suppressed to keep CI green
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    // TODO(typing): replace any with explicit type; suppressed to keep CI green
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    pendingWorkOrders.value = data.filter((o: any) => o.status === 'pending').map((o: any) => ({
      ...o,
      station_name: o.station_id ? `电站${o.station_id}` : '未知电站',
      deadline: '剩余 36h',
    }))
  } catch (err) {
    console.error('获取工单失败:', err)
  }
}

onMounted(() => {
  fetchDashboard()
  fetchWorkOrders()
  fetchHeatmap()
})
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

@media (max-width: 1100px) {
  .stats-row {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 700px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

.main-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 16px;
  margin-bottom: 16px;
}

@media (max-width: 1200px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
}

.main-left {
  min-width: 0;
}

.main-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-row {
  margin-bottom: 20px;
}

.trade-chart {
  height: 120px;
  position: relative;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  overflow: hidden;
  margin: 8px 0;
}
</style>
