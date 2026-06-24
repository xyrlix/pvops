<template>
  <div class="inverter-card" :class="{ offline: status === 'offline' }">
    <div class="inverter-header">
      <div class="inverter-name">{{ name }}</div>
      <PvTag :type="status === 'online' ? 'running' : 'offline'" :label="status === 'online' ? '在线' : '离线'" size="small" />
    </div>
    <div class="inverter-power">
      <span class="power-value">{{ activePower.toFixed(2) }}</span>
      <span class="power-unit">kW</span>
    </div>
    <div class="inverter-meta">
      <div class="meta-item">
        <span class="meta-label">日发电</span>
        <span class="meta-value">{{ dailyEnergy.toFixed(2) }} kWh</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">利用率</span>
        <span class="meta-value">{{ (utilization * 100).toFixed(1) }}%</span>
      </div>
    </div>
    <div class="utilization-bar">
      <div class="utilization-fill" :style="{ width: `${Math.min(utilization * 100, 100)}%`, background: barColor }" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import PvTag from './PvTag.vue'

const props = defineProps<{
  name: string
  activePower: number
  dailyEnergy: number
  utilization: number
  status: string
}>()

const barColor = computed(() => {
  const u = props.utilization * 100
  if (u >= 80) return 'var(--pv-success)'
  if (u >= 50) return 'var(--pv-warning)'
  return 'var(--pv-danger)'
})
</script>

<style scoped>
.inverter-card {
  padding: 18px;
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(16, 24, 40, 0.9), rgba(8, 12, 22, 0.8));
  border: 1px solid var(--pv-border);
  transition: var(--pv-transition);
}

.inverter-card:hover {
  transform: translateY(-4px);
  border-color: rgba(0, 240, 255, 0.25);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4), var(--pv-glow-primary);
}

.inverter-card.offline {
  opacity: 0.7;
}

.inverter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.inverter-name {
  font-weight: 700;
  color: var(--pv-text-primary);
}

.inverter-power {
  margin-bottom: 14px;
}

.power-value {
  font-size: 32px;
  font-weight: 900;
  font-family: var(--pv-font-display);
  color: var(--pv-text-primary);
}

.power-unit {
  font-size: 14px;
  color: var(--pv-text-tertiary);
  margin-left: 6px;
}

.inverter-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 14px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 12px;
  color: var(--pv-text-tertiary);
}

.meta-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--pv-text-secondary);
}

.utilization-bar {
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.utilization-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 1s ease;
  box-shadow: 0 0 10px currentColor;
}
</style>
