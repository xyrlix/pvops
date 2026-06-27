<template>
  <PvCard
    class="agent-digest-card"
    :title="cardTitle"
    :subtitle="cardSubtitle"
    icon="MagicStick"
    glow
    :loading="loading"
  >
    <template #actions>
      <el-button
        size="small"
        :icon="Refresh"
        :loading="loading"
        @click="refresh(true)"
      >
        刷新
      </el-button>
      <el-button
        size="small"
        :icon="vanished ? View : Hide"
        @click="vanished = !vanished"
      >
        {{ vanished ? '展开' : '收起' }}
      </el-button>
    </template>

    <PvEmpty
      v-if="!items.length"
      description="智能体暂无待办事项（系统运行良好）"
    />

    <div v-else-if="!vanished" class="digest-list">
      <div
        v-for="(item, idx) in items"
        :key="idx"
        class="digest-item"
        :class="`digest-item--${item.level}`"
        @click="handleAction(item)"
      >
        <div class="digest-item__head">
          <span class="digest-tag" :class="`tag-${item.level}`">
            {{ levelLabel(item.level) }}
          </span>
          <span class="digest-cat">{{ categoryLabel(item.category) }}</span>
          <span class="digest-title">{{ item.title }}</span>
        </div>
        <div class="digest-item__detail">{{ item.detail }}</div>
        <div v-if="item.action" class="digest-item__action">
          <el-icon><Aim /></el-icon>{{ item.action }}
        </div>
      </div>
    </div>

    <div v-if="!vanished && items.length" class="digest-footer">
      <span>智能体: <strong>{{ agent }}</strong></span>
      <span> · </span>
      <span>更新于 {{ generatedAt }}</span>
      <span v-if="rawSummary"> · 共扫描 {{ rawSummary.critical_alarms_count }} 条告警 / {{ rawSummary.outstanding_workorders_count }} 个工单</span>
    </div>
  </PvCard>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, View, Hide, Aim } from '@element-plus/icons-vue'
import PvCard from './PvCard.vue'
import PvEmpty from './PvEmpty.vue'

interface DigestItem {
  level: 'critical' | 'warning' | 'info'
  category: 'alarm' | 'health' | 'workorder' | 'knowledge' | 'summary'
  title: string
  detail: string
  action?: string
  ref?: { type: 'alarm' | 'station' | 'workorder' | 'doc'; id: number }
}

interface DigestResponse {
  items: DigestItem[]
  generated_at: string
  agent: string
  raw_summary?: {
    critical_alarms_count?: number
    outstanding_workorders_count?: number
    stations_with_alerts?: number
    new_docs_count?: number
  }
}

import { agentApi } from '@/services/api'

const router = useRouter()

const items = ref<DigestItem[]>([])
const agent = ref('')
const generatedAt = ref('')
const rawSummary = ref<DigestResponse['raw_summary']>(undefined)
const loading = ref(false)
const vanished = ref(false)
const POLL_MS = 5 * 60 * 1000 // 5 分钟

let timer: ReturnType<typeof setInterval> | null = null

const cardTitle = computed(() =>
  loading.value && !items.value.length ? '智能体巡检中…' : '🔔 智能体日报'
)
const cardSubtitle = computed(() => {
  if (!items.value.length) return '今日暂无紧急待办'
  const critical = items.value.filter((i) => i.level === 'critical').length
  const warning = items.value.filter((i) => i.level === 'warning').length
  const parts: string[] = []
  if (critical) parts.push(`🔴 ${critical} 紧急`)
  if (warning) parts.push(`⚠️ ${warning} 警告`)
  return parts.length ? parts.join(' · ') : '🟢 一切正常'
})

const levelLabel = (l: string) => {
  const map: Record<string, string> = {
    critical: '紧急',
    warning: '警告',
    info: '信息',
  }
  return map[l] || l
}
const categoryLabel = (c: string) => {
  const map: Record<string, string> = {
    alarm: '告警',
    health: '健康',
    workorder: '工单',
    knowledge: '知识',
    summary: '总览',
  }
  return map[c] || c
}

const handleAction = (item: DigestItem) => {
  const ref = item.ref
  if (!ref) {
    return
  }
  if (ref.type === 'alarm') {
    router.push(`/alarms`)
  } else if (ref.type === 'station') {
    router.push(`/stations/${ref.id}`)
  } else if (ref.type === 'workorder') {
    router.push(`/workorders`)
  } else if (ref.type === 'doc') {
    router.push(`/knowledge`)
  }
}

const refresh = async (manual = false) => {
  if (loading.value) return
  loading.value = true
  try {
    const res = (await agentApi.getBriefing()) as unknown as DigestResponse
    items.value = res.items || []
    agent.value = res.agent
    generatedAt.value = res.generated_at
    rawSummary.value = res.raw_summary
    if (manual) {
      // 静默刷新
    }
  } catch (err) {
    console.error('[AgentDigest] 拉取失败:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refresh(false)
  timer = setInterval(() => refresh(false), POLL_MS)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.agent-digest-card {
  margin-bottom: 20px;
}

.digest-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.digest-item {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid var(--pv-border);
  background: rgba(96, 165, 250, 0.04);
  cursor: pointer;
  transition: var(--pv-transition);
}

.digest-item:hover {
  border-color: var(--pv-primary);
  background: rgba(96, 165, 250, 0.1);
  transform: translateX(4px);
}

.digest-item--critical {
  border-left: 3px solid var(--pv-danger);
  background: rgba(248, 113, 113, 0.08);
}
.digest-item--warning {
  border-left: 3px solid var(--pv-warning);
  background: rgba(251, 191, 36, 0.06);
}
.digest-item--info {
  border-left: 3px solid var(--pv-info);
}

.digest-item__head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.digest-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-family: var(--pv-font-mono);
}
.tag-critical {
  background: var(--pv-danger);
  color: #fff;
}
.tag-warning {
  background: var(--pv-warning);
  color: #0B1120;
}
.tag-info {
  background: var(--pv-info);
  color: #0B1120;
}

.digest-cat {
  font-size: 11px;
  color: var(--pv-text-tertiary);
  font-family: var(--pv-font-mono);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.digest-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--pv-text-primary);
  flex: 1;
  min-width: 0;
}

.digest-item__detail {
  font-size: 12px;
  color: var(--pv-text-secondary);
  margin-bottom: 4px;
  font-family: var(--pv-font-mono);
}

.digest-item__action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--pv-primary);
  font-weight: 600;
}

.digest-footer {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--pv-border);
  font-size: 11px;
  color: var(--pv-text-tertiary);
  font-family: var(--pv-font-mono);
}
.digest-footer strong {
  color: var(--pv-primary);
}
</style>