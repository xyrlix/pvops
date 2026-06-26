<template>
  <el-card
    class="pv-card"
    :class="{ 'pv-card-glow': glow, 'is-loading': loading }"
    shadow="never"
    :body-style="bodyStyle"
  >
    <template v-if="$slots.header || title" #header>
      <div class="pv-card-header">
        <div class="pv-card-title-wrap">
          <span v-if="title" class="pv-card-title">
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
    title: '',
    subtitle: '',
    icon: '',
    emptyText: '',
    bodyStyle: () => ({}),
    skeletonVariant: 'chart',
    skeletonRows: 3,
  }
)
</script>

<style scoped>
.pv-card {
  border-radius: var(--pv-radius);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: var(--pv-transition);
  --el-card-padding: 0;
}

.pv-card:hover {
  border-color: rgba(255, 255, 255, 0.1);
}

.pv-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.pv-card-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.pv-card-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  display: flex;
  align-items: center;
  gap: 8px;
}

.pv-card-icon {
  color: var(--pv-primary);
}

.pv-card-title-text {
  font-family: var(--pv-font-body);
  font-weight: 600;
}

.pv-card-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
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

:deep(.el-card__body) {
  padding: 18px;
}
</style>
