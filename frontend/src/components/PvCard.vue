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
            <el-icon v-if="icon" :size="18"><component :is="icon" /></el-icon>
            {{ title }}
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

.pv-card:hover {
  border-color: rgba(0, 240, 255, 0.25);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), var(--pv-glow-primary);
  transform: translateY(-2px);
}

.pv-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.pv-card-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.pv-card-title {
  font-size: 16px;
  font-weight: 800;
  color: var(--pv-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.pv-card-subtitle {
  font-size: 12px;
  color: var(--pv-text-tertiary);
  font-weight: 500;
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
