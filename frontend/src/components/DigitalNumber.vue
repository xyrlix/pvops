<template>
  <div class="digital-number" :style="{ color, textShadow: glow }">
    <span class="value">{{ displayValue }}</span>
    <span v-if="unit" class="unit">{{ unit }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  value: number | string | null | undefined
  unit?: string
  color?: string
  decimals?: number
}>()

const displayValue = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') return '--'
  if (typeof props.value === 'number') return props.value.toFixed(props.decimals ?? 1)
  return String(props.value)
})

const glow = computed(() => `0 0 20px ${props.color || '#00f0ff'}88, 0 0 40px ${props.color || '#00f0ff'}44`)
</script>

<style scoped>
.digital-number {
  font-family: 'DIN Alternate', 'Roboto Mono', 'Helvetica Neue', sans-serif;
  font-weight: 900;
  font-size: 42px;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.unit {
  font-size: 16px;
  font-weight: 600;
  color: var(--pv-text-tertiary);
}
</style>
