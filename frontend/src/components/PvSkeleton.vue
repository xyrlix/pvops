<template>
  <div class="pv-skeleton" :class="[`variant-${variant}`, { animated }]">
    <template v-if="variant === 'text' || variant === 'paragraph'">
      <div
        v-for="i in rows"
        :key="i"
        class="skeleton-line"
        :style="{ width: i === rows && lastLineWidth ? lastLineWidth : undefined }"
      />
    </template>
    <template v-else-if="variant === 'card'">
      <div class="skeleton-header">
        <div class="skeleton-avatar" v-if="avatar" />
        <div class="skeleton-title" />
      </div>
      <div class="skeleton-line" v-for="i in rows" :key="i" />
    </template>
    <template v-else-if="variant === 'chart'">
      <div class="skeleton-title" style="width: 40%; margin-bottom: 16px" />
      <div class="skeleton-chart" />
    </template>
    <template v-else-if="variant === 'table'">
      <div class="skeleton-row header" />
      <div class="skeleton-row" v-for="i in rows" :key="i" />
    </template>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'text' | 'paragraph' | 'card' | 'chart' | 'table'
    rows?: number
    lastLineWidth?: string
    avatar?: boolean
    animated?: boolean
  }>(),
  {
    variant: 'text',
    rows: 3,
    lastLineWidth: '60%',
    avatar: false,
    animated: true,
  }
)
</script>

<style scoped>
.pv-skeleton {
  --skeleton-bg: rgba(15, 23, 42, 0.08);
  --skeleton-highlight: rgba(15, 23, 42, 0.15);
}

html.dark .pv-skeleton {
  --skeleton-bg: rgba(255, 255, 255, 0.06);
  --skeleton-highlight: rgba(255, 255, 255, 0.12);
}

.skeleton-line,
.skeleton-title,
.skeleton-avatar,
.skeleton-chart,
.skeleton-row {
  background: var(--skeleton-bg);
  border-radius: 6px;
}

.animated .skeleton-line,
.animated .skeleton-title,
.animated .skeleton-avatar,
.animated .skeleton-chart,
.animated .skeleton-row {
  background: linear-gradient(
    90deg,
    var(--skeleton-bg) 25%,
    var(--skeleton-highlight) 50%,
    var(--skeleton-bg) 75%
  );
  background-size: 200% 100%;
  animation: pv-skeleton-flow 1.5s infinite;
}

@keyframes pv-skeleton-flow {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.variant-paragraph .skeleton-line,
.variant-text .skeleton-line {
  height: 14px;
  margin-bottom: 10px;
}

.variant-text .skeleton-line:last-child,
.variant-paragraph .skeleton-line:last-child {
  margin-bottom: 0;
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
}

.skeleton-title {
  height: 18px;
  width: 35%;
}

.skeleton-chart {
  height: 180px;
  border-radius: var(--pv-radius-sm);
}

.skeleton-row {
  height: 40px;
  margin-bottom: 8px;
}

.skeleton-row.header {
  height: 44px;
  margin-bottom: 12px;
}
</style>
