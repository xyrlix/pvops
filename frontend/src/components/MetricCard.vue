<template>
  <el-card class="metric-card pv-card-glow" shadow="hover" :body-style="{ padding: '22px' }">
    <div v-if="loading" class="metric-skeleton">
      <div class="pv-skeleton" style="height: 20px; width: 40%; margin-bottom: 18px" />
      <div class="pv-skeleton" style="height: 42px; width: 70%; margin-bottom: 12px" />
      <div class="pv-skeleton" style="height: 16px; width: 50%" />
    </div>
    <template v-else>
      <div class="metric-header">
        <div class="icon-wrap" :style="{ background: iconBg, boxShadow: iconGlow }">
          <el-icon :size="24" :color="iconColor">
            <component :is="icon" />
          </el-icon>
        </div>
        <span class="metric-title">{{ title }}</span>
      </div>
      <div class="metric-value" :style="{ color: valueColor, textShadow: valueGlow }">
        {{ animatedValue }}
        <span v-if="unit" class="metric-unit">{{ unit }}</span>
      </div>
      <div class="metric-footer">
        <div v-if="subtitle" class="metric-subtitle">{{ subtitle }}</div>
        <div v-if="trend !== undefined" class="metric-trend" :class="trend >= 0 ? 'up' : 'down'">
          <el-icon><ArrowUp v-if="trend >= 0" /><ArrowDown v-else /></el-icon>
          {{ Math.abs(trend).toFixed(1) }}%
        </div>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowUp, ArrowDown } from '@element-plus/icons-vue'

const props = defineProps<{
  title: string
  value: number | string | null | undefined
  unit?: string
  subtitle?: string
  icon: string
  iconColor?: string
  valueColor?: string
  iconBg?: string
  trend?: number
  decimals?: number
  loading?: boolean
  enableAnimation?: boolean
}>()

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

const valueGlow = computed(() => `0 0 18px ${props.valueColor}66`)
const iconGlow = computed(() => `0 4px 20px ${props.iconColor || '#00f0ff'}44`)
</script>

<style scoped>
.metric-card {
  position: relative;
  overflow: hidden;
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(16, 24, 40, 0.9), rgba(8, 12, 22, 0.8));
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, v-bind(valueColor), transparent);
  opacity: 0.8;
  animation: top-glow 3s linear infinite;
}

@keyframes top-glow {
  0% { opacity: 0.4; }
  50% { opacity: 1; }
  100% { opacity: 0.4; }
}

.metric-card:hover {
  transform: translateY(-5px);
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.icon-wrap {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.metric-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--pv-text-secondary);
}

.metric-value {
  font-size: 36px;
  font-weight: 900;
  margin-bottom: 10px;
  letter-spacing: -0.5px;
  font-family: var(--pv-font-display);
}

.metric-unit {
  font-size: 14px;
  font-weight: 500;
  color: var(--pv-text-tertiary);
  margin-left: 6px;
}

.metric-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.metric-subtitle {
  font-size: 12px;
  color: var(--pv-text-tertiary);
}

.metric-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
}

.metric-trend.up {
  color: var(--pv-success);
  background: rgba(0, 255, 157, 0.1);
  box-shadow: 0 0 12px rgba(0, 255, 157, 0.15);
}

.metric-trend.down {
  color: var(--pv-danger);
  background: rgba(255, 42, 109, 0.1);
  box-shadow: 0 0 12px rgba(255, 42, 109, 0.15);
}

.metric-skeleton {
  padding: 4px 0;
}
</style>
