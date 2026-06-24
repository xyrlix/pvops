<template>
  <el-card class="station-card" shadow="hover">
    <div class="station-info">
      <h3>{{ station.name }}</h3>
      <p>{{ station.location || '未设置位置' }}</p>
      <p>容量：{{ station.capacity_kw }} kW</p>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { Station } from '@/types/station'

defineProps<{
  station: Station
}>()
</script>

<style scoped>
.station-card {
  margin-bottom: 16px;
}

.station-info h3 {
  margin: 0 0 8px 0;
  color: var(--pv-text-primary);
}

.station-info p {
  margin: 4px 0;
  color: var(--pv-text-secondary);
  font-size: 14px;
}
</style>
