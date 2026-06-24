<template>
  <el-card class="alarm-panel" shadow="hover" :body-style="{ padding: '20px' }">
    <template #header>
      <div class="panel-header">
        <span class="panel-title">
          <el-icon><Warning /></el-icon>
          告警面板
        </span>
        <el-tag v-if="alarms.length > 0" type="danger" effect="dark" class="alarm-count">{{ alarms.length }} 条</el-tag>
        <el-tag v-else type="success" effect="dark">运行正常</el-tag>
      </div>
    </template>
    <el-timeline v-if="alarms.length > 0">
      <el-timeline-item
        v-for="alarm in alarms"
        :key="alarm.id"
        :type="alarm.type"
        :timestamp="alarm.time"
      >
        <div class="alarm-item" :class="{ critical: alarm.type === 'danger' }">
          <div class="alarm-title">{{ alarm.title }}</div>
          <div class="alarm-desc">{{ alarm.description }}</div>
        </div>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else description="暂无告警" />
  </el-card>
</template>

<script setup lang="ts">
import { Warning } from '@element-plus/icons-vue'

interface Alarm {
  id: number
  title: string
  description: string
  time: string
  type: 'primary' | 'success' | 'warning' | 'danger'
}

defineProps<{
  alarms: Alarm[]
}>()
</script>

<style scoped>
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
  font-size: 16px;
  color: var(--pv-text-primary);
}

.alarm-count {
  animation: danger-pulse 1.8s ease-in-out infinite;
}

@keyframes danger-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 42, 109, 0.5); }
  50% { box-shadow: 0 0 0 8px rgba(255, 42, 109, 0); }
}

.alarm-item {
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid transparent;
  transition: all 0.2s;
}

.alarm-item.critical {
  background: rgba(255, 42, 109, 0.08);
  border-color: rgba(255, 42, 109, 0.25);
  box-shadow: 0 0 16px rgba(255, 42, 109, 0.15);
}

.alarm-title {
  font-weight: 700;
  color: var(--pv-text-primary);
  margin-bottom: 4px;
}

.alarm-desc {
  font-size: 13px;
  color: var(--pv-text-secondary);
  line-height: 1.5;
}

:deep(.el-timeline-item__node) {
  box-shadow: 0 0 0 4px rgba(0, 240, 255, 0.15);
}

:deep(.el-timeline-item__timestamp) {
  color: var(--pv-text-tertiary);
  font-size: 12px;
}
</style>
