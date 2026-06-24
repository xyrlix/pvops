<template>
  <DashboardLayout>
    <template #breadcrumb>
      <el-icon class="back-icon" :size="22"><Warning /></el-icon>
      <span>告警中心</span>
    </template>

    <!-- 统计卡 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card danger">
          <div class="stat-value">
            <PvSkeleton v-if="statsLoading" variant="text" :rows="1" />
            <template v-else>{{ stats.open }}</template>
          </div>
          <div class="stat-label">未处理</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card warning">
          <div class="stat-value">
            <PvSkeleton v-if="statsLoading" variant="text" :rows="1" />
            <template v-else>{{ stats.acknowledged }}</template>
          </div>
          <div class="stat-label">已确认</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card success">
          <div class="stat-value">
            <PvSkeleton v-if="statsLoading" variant="text" :rows="1" />
            <template v-else>{{ stats.closed }}</template>
          </div>
          <div class="stat-label">已关闭</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card info">
          <div class="stat-value">
            <PvSkeleton v-if="statsLoading" variant="text" :rows="1" />
            <template v-else>{{ stats.total }}</template>
          </div>
          <div class="stat-label">今日告警</div>
        </div>
      </el-col>
    </el-row>

    <!-- 分布图 + 聚合 -->
    <el-row :gutter="20" class="section-row">
      <el-col :xs="24" :lg="8">
        <PvCard title="告警等级分布" icon="PieChart" glow :loading="statsLoading">
          <AlarmDonutChart :data="levelDistribution" :height="260" />
        </PvCard>
      </el-col>
      <el-col :xs="24" :lg="16">
        <PvCard title="告警聚合" subtitle="按规则/电站聚合未处理告警" icon="DataLine" glow>
          <el-table :data="summary" stripe>
            <el-table-column prop="rule_name" label="规则" min-width="180" />
            <el-table-column prop="level" label="等级" width="100">
              <template #default="{ row }">
                <PvTag :type="row.level === 'critical' ? 'urgent' : 'high'" :label="row.level === 'critical' ? '严重' : '警告'" />
              </template>
            </el-table-column>
            <el-table-column prop="station_id" label="电站ID" width="100" />
            <el-table-column prop="count" label="发生次数" width="110" />
            <el-table-column prop="latest_at" label="最近时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.latest_at) }}
              </template>
            </el-table-column>
          </el-table>
        </PvCard>
      </el-col>
    </el-row>

    <!-- 告警列表 -->
    <el-row class="section-row">
      <el-col :span="24">
        <PvCard title="告警列表" icon="Warning" glow>
          <template #actions>
            <el-radio-group v-model="filterStatus" size="small" @change="fetchAlarms">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="open">未处理</el-radio-button>
              <el-radio-button label="acknowledged">已确认</el-radio-button>
              <el-radio-button label="closed">已关闭</el-radio-button>
            </el-radio-group>
            <el-button
              v-if="selectedAlarms.length"
              size="small"
              type="primary"
              @click="batchAck"
            >批量确认</el-button>
            <el-button
              v-if="selectedAlarms.length"
              size="small"
              type="danger"
              @click="batchClose"
            >批量关闭</el-button>
          </template>
          <el-table
            :data="alarms"
            stripe
            v-loading="loading"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="50" />
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="title" label="告警标题" min-width="180" />
            <el-table-column prop="level" label="等级" width="90">
              <template #default="{ row }">
                <PvTag :type="row.level === 'critical' ? 'urgent' : row.level === 'warning' ? 'high' : 'medium'" :label="levelText(row.level)" />
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="90">
              <template #default="{ row }">
                <PvTag :type="row.priority" :label="priorityText(row.priority)" />
              </template>
            </el-table-column>
            <el-table-column prop="rule_name" label="规则" width="130" />
            <el-table-column prop="description" label="描述" min-width="220" />
            <el-table-column prop="created_at" label="发生时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <PvTag :type="row.status === 'open' ? 'danger' : row.status === 'acknowledged' ? 'warning' : 'success'" :label="statusText(row.status)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="260" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.status !== 'closed'"
                  size="small"
                  type="primary"
                  @click="createWorkOrder(row)"
                >创建工单</el-button>
                <el-button
                  v-if="row.status === 'open'"
                  size="small"
                  @click="ackAlarm(row.id)"
                >确认</el-button>
                <el-button
                  v-if="row.status !== 'closed'"
                  size="small"
                  type="danger"
                  plain
                  @click="closeAlarm(row.id)"
                >关闭</el-button>
                <el-button
                  size="small"
                  type="info"
                  plain
                  @click="askAi(row)"
                >问 AI</el-button>
              </template>
            </el-table-column>
          </el-table>
        </PvCard>
      </el-col>
    </el-row>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Warning } from '@element-plus/icons-vue'
import DashboardLayout from '@/components/DashboardLayout.vue'
import PvCard from '@/components/PvCard.vue'
import PvTag from '@/components/PvTag.vue'
import PvSkeleton from '@/components/PvSkeleton.vue'
import AlarmDonutChart from '@/components/AlarmDonutChart.vue'
import { alarmApi } from '@/services/api'
import { useCopilotStore } from '@/stores/copilot'
import { ElMessage } from 'element-plus'

const copilotStore = useCopilotStore()
const alarms = ref<any[]>([])
const summary = ref<any[]>([])
const loading = ref(false)
const statsLoading = ref(false)
const filterStatus = ref('')
const selectedAlarms = ref<any[]>([])

const stats = computed(() => {
  const total = alarms.value.length
  const open = alarms.value.filter((a) => a.status === 'open').length
  const acknowledged = alarms.value.filter((a) => a.status === 'acknowledged').length
  const closed = alarms.value.filter((a) => a.status === 'closed').length
  return { total, open, acknowledged, closed }
})

const levelDistribution = computed(() => {
  const map: Record<string, number> = {}
  alarms.value.forEach((a) => {
    const key = a.level === 'critical' ? '严重' : a.level === 'warning' ? '警告' : '一般'
    map[key] = (map[key] || 0) + 1
  })
  return Object.entries(map).map(([name, value]) => ({ name, value }))
})

const levelText = (level: string) => {
  const map: Record<string, string> = { critical: '严重', warning: '警告', info: '一般' }
  return map[level] || level
}

const priorityText = (p: string) => {
  const map: Record<string, string> = { urgent: '紧急', high: '高', medium: '中', low: '低' }
  return map[p] || p
}

const statusText = (s: string) => {
  const map: Record<string, string> = { open: '未处理', acknowledged: '已确认', closed: '已关闭' }
  return map[s] || s
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

const fetchAlarms = async () => {
  loading.value = true
  statsLoading.value = true
  try {
    const [data, sumData] = await Promise.all([
      alarmApi.list(undefined, filterStatus.value || undefined),
      alarmApi.summary(),
    ])
    alarms.value = data as unknown as any[]
    summary.value = sumData as unknown as any[]
  } catch (err) {
    console.error('获取告警失败:', err)
  } finally {
    loading.value = false
    statsLoading.value = false
  }
}

const handleSelectionChange = (val: any[]) => {
  selectedAlarms.value = val
}

const ackAlarm = async (id: number) => {
  try {
    await alarmApi.ack(id)
    ElMessage.success('告警已确认')
    fetchAlarms()
  } catch {
    ElMessage.error('确认失败')
  }
}

const closeAlarm = async (id: number) => {
  try {
    await alarmApi.close(id)
    ElMessage.success('告警已关闭')
    fetchAlarms()
  } catch {
    ElMessage.error('关闭失败')
  }
}

const batchAck = async () => {
  await Promise.all(selectedAlarms.value.map((a) => alarmApi.ack(a.id)))
  ElMessage.success('批量确认成功')
  fetchAlarms()
}

const batchClose = async () => {
  await Promise.all(selectedAlarms.value.map((a) => alarmApi.close(a.id)))
  ElMessage.success('批量关闭成功')
  fetchAlarms()
}

const createWorkOrder = async (alarm: any) => {
  try {
    const res: any = await alarmApi.createWorkOrder(alarm.id)
    if (res.success) {
      ElMessage.success('工单创建成功')
      fetchAlarms()
    } else {
      ElMessage.warning(res.message || '已存在关联工单')
    }
  } catch {
    ElMessage.error('创建工单失败')
  }
}

const askAi = (alarm: any) => {
  copilotStore.open({
    type: 'alarm',
    station_id: alarm.station_id,
    alarm_title: alarm.title,
    alarm_description: alarm.description,
  })
}

onMounted(() => {
  fetchAlarms()
})
</script>

<style scoped>
.stats-row {
  margin-bottom: 22px;
}

.stat-card {
  padding: 18px;
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(16, 24, 40, 0.9), rgba(8, 12, 22, 0.8));
  border: 1px solid var(--pv-border);
  text-align: center;
  position: relative;
  overflow: hidden;
  transition: var(--pv-transition);
}

.stat-card:hover {
  transform: translateY(-3px);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.stat-card.danger::before { background: var(--pv-danger); box-shadow: 0 0 12px var(--pv-danger); }
.stat-card.warning::before { background: var(--pv-warning); box-shadow: 0 0 12px var(--pv-warning); }
.stat-card.success::before { background: var(--pv-success); box-shadow: 0 0 12px var(--pv-success); }
.stat-card.info::before { background: var(--pv-info); box-shadow: 0 0 12px var(--pv-info); }

.stat-value {
  font-size: 30px;
  font-weight: 900;
  font-family: var(--pv-font-display);
  color: var(--pv-text-primary);
  margin-bottom: 6px;
}

.stat-label {
  font-size: 13px;
  color: var(--pv-text-secondary);
}

.section-row {
  margin-bottom: 22px;
}
</style>
