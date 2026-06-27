<template>
  <DashboardLayout>
    <template #title>
      <span class="pv-page-title">AI 智能体</span>
    </template>
    <template #subtitle>AI AGENT · 主动感知 + 自动闭环</template>

    <template #actions>
      <el-button :icon="Refresh" :loading="loadingBriefing" @click="fetchBriefing">刷新简报</el-button>
    </template>

    <!-- 智能体日报 -->
    <AgentDigestCard />

    <!-- 能力卡片 -->
    <el-row :gutter="20" class="cap-row">
      <el-col :xs="24" :sm="12" :md="6">
        <PvCard title="每日巡检" icon="Warning" glow>
          <p style="font-size:13px;color:var(--pv-text-secondary);margin:0 0 12px">AI 每日自动扫描电站状态、告警、工单，推送 3-5 条值得关注的事项</p>
          <el-button size="small" plain @click="$router.push('/')">查看日报</el-button>
        </PvCard>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <PvCard title="一键诊断" icon="Cpu" glow>
          <p style="font-size:13px;color:var(--pv-text-secondary);margin:0 0 12px">选择电站自动跑全链路诊断：规则引擎 + LLM 润色 + 证据链 + 修复建议</p>
          <el-button size="small" plain @click="$router.push('/stations')">去诊断</el-button>
        </PvCard>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <PvCard title="自动工单" icon="Tickets" glow>
          <p style="font-size:13px;color:var(--pv-text-secondary);margin:0 0 12px">诊断发现 critical/warning 异常时，AI 自动创建工单并分配优先级</p>
          <el-button size="small" plain @click="$router.push('/workorders')">查看工单</el-button>
        </PvCard>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <PvCard title="知识沉淀" icon="Collection" glow>
          <p style="font-size:13px;color:var(--pv-text-secondary);margin:0 0 12px">已处理的工单案例自动归档到知识库，下次同类问题 AI 可直接检索</p>
          <el-button size="small" plain @click="$router.push('/knowledge')">去知识库</el-button>
        </PvCard>
      </el-col>
    </el-row>

    <!-- 对话记录 -->
    <PvCard title="近期 AI 对话" icon="ChatDotRound" glow>
      <PvEmpty v-if="!history.length" description="暂无对话历史，点击右下角 AI 助手开始对话" />
      <div v-else class="history-list">
        <div v-for="(h, i) in history" :key="i" class="history-item">
          <div class="history-q">{{ h.question }}</div>
          <div class="history-a">{{ truncate(h.answer, 120) }}</div>
          <div class="history-time">{{ new Date(h.time).toLocaleString('zh-CN') }}</div>
        </div>
      </div>
    </PvCard>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import DashboardLayout from '@/components/DashboardLayout.vue'
import AgentDigestCard from '@/components/AgentDigestCard.vue'
import PvCard from '@/components/PvCard.vue'
import PvEmpty from '@/components/PvEmpty.vue'

const loadingBriefing = ref(false)
const history = ref<Array<{ question: string; answer: string; time: string }>>([])

const truncate = (val: string, max = 120) =>
  val.length > max ? val.slice(0, max) + '...' : val

const fetchBriefing = async () => {
  loadingBriefing.value = true
  // AgentDigestCard 自身有轮询，这里只做手动触发
  setTimeout(() => { loadingBriefing.value = false }, 1000)
}

// 从 localStorage 读取会话历史
try {
  const raw = localStorage.getItem('pvops-chat-history')
  if (raw) history.value = JSON.parse(raw).slice(0, 20)
} catch { /* ignore */ }
</script>

<style scoped>
.cap-row { margin-bottom: 22px; }
.cap-row p { line-height: 1.6; }
.history-list { display: flex; flex-direction: column; gap: 12px; }
.history-item {
  padding: 12px 16px;
  border-radius: 10px;
  border: 1px solid var(--pv-border);
  background: var(--pv-surface);
}
.history-q { font-weight: 600; font-size: 14px; margin-bottom: 4px; color: var(--pv-text-primary); }
.history-a { font-size: 13px; color: var(--pv-text-secondary); margin-bottom: 4px; }
.history-time { font-size: 11px; color: var(--pv-text-tertiary); font-family: var(--pv-font-mono); }
</style>