<template>
  <div class="metric-card" :class="{ 'metric-card--glow': glow }">
    <div class="metric-card__head">
      <div class="icon-wrap" :style="{ background: iconBg, boxShadow: iconGlow }">
        <el-icon :size="22" :color="iconColor">
          <component :is="icon" />
        </el-icon>
      </div>
      <div class="metric-card__title">
        <span>{{ title }}</span>
        <span v-if="hint" class="metric-card__hint">{{ hint }}</span>
      </div>
      <span v-if="trend !== undefined" class="metric-trend" :class="trend >= 0 ? 'up' : 'down'">
        <el-icon><CaretTop v-if="trend >= 0" /><CaretBottom v-else /></el-icon>
        {{ Math.abs(trend).toFixed(1) }}%
      </span>
    </div>

    <div v-if="loading" class="metric-skeleton">
      <div class="pv-skeleton" style="height: 36px; width: 60%; margin-bottom: 10px" />
      <div class="pv-skeleton" style="height: 14px; width: 40%" />
    </div>
    <template v-else>
      <div class="metric-value" :style="{ color: valueColor }">
        <span class="metric-value__num">{{ animatedValue }}</span>
        <span v-if="unit" class="metric-unit">{{ unit }}</span>
      </div>
      <div v-if="subtitle" class="metric-subtitle">{{ subtitle }}</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { CaretTop, CaretBottom } from '@element-plus/icons-vue'

const props = withDefaults(
  defineProps<{
    title: string
    value: number | string | null | undefined
    unit?: string
    subtitle?: string
    hint?: string
    icon: string
    iconColor?: string
    valueColor?: string
    iconBg?: string
    trend?: number
    decimals?: number
    loading?: boolean
    glow?: boolean
    enableAnimation?: boolean
  }>(),
  {
    unit: '',
    subtitle: '',
    hint: '',
    trend: 0,
    iconColor: 'var(--pv-primary)',
    valueColor: 'var(--pv-text-primary)',
    iconBg: 'linear-gradient(135deg, rgba(34,211,238,0.18), rgba(34,211,238,0.04))',
    glow: false,
    decimals: 1,
  }
)

const rawValue = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') {
    return null
  }
  return typeof props.value === 'number' ? props.value : Number(props.value)
})

const animatedValue = ref<string>('--')
let rafId: number | null = null

function animate(target: number) {
  if (rafId) cancelAnimationFrame(rafId)
  const duration = 1200
  const start = performance.now()
  const from = 0

  const step = (now: number) => {
    const p = Math.min((now - start) / duration, 1)
    const eased = 1 - Math.pow(1 - p, 4)
    const current = from + (target - from) * eased
    animatedValue.value = current.toFixed(props.decimals ?? 1)
    if (p < 1) {
      rafId = requestAnimationFrame(step)
    }
  }
  rafId = requestAnimationFrame(step)
}

watch(
  () => props.value,
  () => {
    if (props.loading) {
      animatedValue.value = '--'
      return
    }
    if (rawValue.value === null || Number.isNaN(rawValue.value)) {
      animatedValue.value = typeof props.value === 'string' ? props.value : '--'
      return
    }
    if (props.enableAnimation !== false) {
      animate(rawValue.value)
    } else {
      animatedValue.value = rawValue.value.toFixed(props.decimals ?? 1)
    }
  },
  { immediate: true }
)

const iconGlow = computed(() => `0 4px 18px ${props.iconColor}55`)
</script>

<style scoped>
.metric-card {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  background: var(--pv-surface);
  border: 1px solid var(--pv-border);
  padding: 18px 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: var(--pv-transition);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

html.dark .metric-card {
  background: linear-gradient(180deg, rgba(15, 27, 45, 0.72), rgba(10, 18, 32, 0.6));
}

.metric-card:hover {
  border-color: var(--pv-border-strong);
  box-shadow: var(--pv-shadow-lg);
}

.metric-card--glow::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.45), transparent 60%, rgba(129, 140, 248, 0.35));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

.metric-card__head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-card__title {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.metric-card__title > span:first-child {
  font-size: 12px;
  font-weight: 600;
  font-family: var(--pv-font-mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--pv-text-tertiary);
}

.metric-card__hint {
  font-size: 10px;
  color: var(--pv-text-tertiary);
  margin-top: 2px;
  letter-spacing: 0.04em;
}

.metric-trend {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 11px;
  font-weight: 600;
  font-family: var(--pv-font-mono);
  padding: 3px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}

.metric-trend.up {
  color: var(--pv-success);
  background: rgba(52, 211, 153, 0.1);
}

.metric-trend.down {
  color: var(--pv-danger);
  background: rgba(244, 63, 94, 0.1);
}

.metric-value {
  display: flex;
  align-items: baseline;
  gap: 6px;
  line-height: 1;
}

.metric-value__num {
  font-family: var(--pv-font-mono);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  font-size: 32px;
  letter-spacing: -0.02em;
  color: var(--pv-text-primary);
}

.metric-unit {
  font-family: var(--pv-font-mono);
  font-size: 13px;
  font-weight: 500;
  color: var(--pv-text-tertiary);
  letter-spacing: 0.02em;
}

.metric-subtitle {
  font-size: 12px;
  color: var(--pv-text-tertiary);
  letter-spacing: 0.02em;
}

.metric-skeleton {
  padding: 4px 0;
}
</style>
