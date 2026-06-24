<template>
  <el-timeline>
    <el-timeline-item
      v-for="(item, index) in timeline"
      :key="index"
      :type="itemType(item.status)"
      :icon="itemIcon(item.status)"
      :timestamp="formatTime(item.created_at)"
    >
      <div class="timeline-status">{{ statusText(item.status) }}</div>
      <div v-if="item.comment" class="timeline-comment">{{ item.comment }}</div>
      <div v-if="item.solution" class="timeline-solution">
        <el-icon><CircleCheck /></el-icon>
        {{ item.solution }}
      </div>
    </el-timeline-item>
  </el-timeline>
</template>

<script setup lang="ts">
import { CircleCheck } from '@element-plus/icons-vue'

defineProps<{
  timeline: { status: string; comment?: string; solution?: string; created_at: string }[]
}>()

const itemType = (status: string) => {
  const map: Record<string, any> = {
    created: 'info',
    pending: 'danger',
    in_progress: 'warning',
    completed: 'success',
  }
  return map[status] || 'info'
}

const itemIcon = (status: string) => {
  return status === 'completed' ? 'CircleCheck' : undefined
}

const statusText = (status: string) => {
  const map: Record<string, string> = {
    created: '工单创建',
    pending: '待处理',
    in_progress: '开始处理',
    completed: '完成工单',
  }
  return map[status] || status
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.timeline-status {
  font-weight: 700;
  color: var(--pv-text-primary);
  margin-bottom: 4px;
}

.timeline-comment {
  font-size: 13px;
  color: var(--pv-text-secondary);
  line-height: 1.5;
}

.timeline-solution {
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(0, 255, 157, 0.08);
  border: 1px solid rgba(0, 255, 157, 0.2);
  font-size: 13px;
  color: var(--pv-success);
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
</style>
