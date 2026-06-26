<template>
  <el-card
    class="pv-card"
    :class="{ 'pv-card-glow': glow, 'is-loading': loading }"
    shadow="hover"
    :body-style="bodyStyle"
  >
    <template #header v-if="$slots.header || title">
      <div class="pv-card-header">
        <div class="pv-card-title-wrap">
          <span v-if="title" class="pv-card-title">
            <span class="pv-card-bar" />
            <el-icon v-if="icon" :size="16" class="pv-card-icon"><component :is="icon" /></el-icon>
            <span class="pv-card-title-text">{{ title }}</span>
          </span>
          <span v-if="subtitle" class="pv-card-subtitle">{{ subtitle }}</span>
          <slot name="title-extra" />
        </div>
        <div class="pv-card-actions">
          <slot name="actions" />
        </div>
      </div>
    </template>
    <div v-if="loading" class="pv-card-loading">
      <PvSkeleton :variant="skeletonVariant" :rows="skeletonRows" />
    </div>
    <div v-else-if="empty" class="pv-card-empty">
      <PvEmpty :description="emptyText" />
    </div>
    <slot v-else />
  </el-card>
</template>

<script setup lang="ts">
import PvEmpty from './PvEmpty.vue'
import PvSkeleton from './PvSkeleton.vue'

withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    icon?: string
    glow?: boolean
    loading?: boolean
    empty?: boolean
    emptyText?: string
    skeletonVariant?: 'text' | 'paragraph' | 'card' | 'chart' | 'table'
    skeletonRows?: number
    bodyStyle?: Record<string, string>
  }>(),
  {
    skeletonVariant: 'chart',
    skeletonRows: 3,
  }
)
</script>

<style scoped>
.pv-card {
  border-radius: var(--pv-radius-lg);
  background: var(--pv-surface);
  border: 1px solid var(--pv-border);
  transition: var(--pv-transition);
}

html.dark .pv-card {
  background: linear-gradient(180deg, rgba(15, 27, 45, 0.72), rgba(10, 18, 32, 0.6));
}

.pv-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  min-height: 32px;
}

.pv-card-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.pv-card-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--pv-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.pv-card-bar {
  display: inline-block;
  width: 3px;
  height: 14px;
  background: linear-gradient(180deg, var(--pv-primary), var(--pv-accent));
  border-radius: 2px;
}

.pv-card-icon {
  color: var(--pv-primary);
}

.pv-card-title-text {
  font-family: var(--pv-font-body);
  font-weight: 700;
}

.pv-card-subtitle {
  font-size: 11px;
  color: var(--pv-text-tertiary);
  font-weight: 500;
  font-family: var(--pv-font-mono);
  letter-spacing: 0.04em;
}

.pv-card-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pv-card-loading {
  padding: 20px 0;
}

.pv-card-empty {
  padding: 30px 0;
}
</style>
