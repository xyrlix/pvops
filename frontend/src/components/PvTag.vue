<template>
  <el-tag :type="tagType" effect="dark" :size="size" class="pv-tag">
    <el-icon v-if="icon" :size="12" class="pv-tag-icon"><component :is="icon" /></el-icon>
    <slot>{{ label }}</slot>
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  type?: string
  label?: string
  icon?: string
  size?: 'small' | 'default' | 'large'
}>()

const tagType = computed(() => {
  const map: Record<string, any> = {
    success: 'success',
    running: 'success',
    online: 'success',
    active: 'success',
    completed: 'success',
    healthy: 'success',
    warning: 'warning',
    in_progress: 'warning',
    acknowledged: 'warning',
   亚健康: 'warning',
    danger: 'danger',
    critical: 'danger',
    urgent: 'danger',
    offline: 'danger',
    inactive: 'info',
    pending: 'info',
    open: 'danger',
    closed: 'info',
    info: 'info',
    medium: 'info',
    low: 'info',
    high: 'warning',
  }
  return map[props.type || ''] || 'info'
})
</script>

<style scoped>
.pv-tag {
  border-radius: 8px;
  font-weight: 600;
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.pv-tag-icon {
  margin-right: 2px;
}
</style>
