<template>
  <el-tree
    :data="treeData"
    :props="defaultProps"
    node-key="id"
    default-expand-all
    :expand-on-click-node="false"
    class="device-tree"
  >
    <template #default="{ data: node }">
      <span class="tree-node">
        <el-icon class="tree-icon" :size="18">
          <component :is="iconFor(node.device_type)" />
        </el-icon>
        <span class="tree-label">{{ node.name }}</span>
        <el-tag size="small" effect="dark" :type="statusType(node.status)">
          {{ node.device_code }}
        </el-tag>
      </span>
    </template>
  </el-tree>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface DeviceNode {
  id: number
  name: string
  device_type: string
  device_code: string
  status: string
  children?: DeviceNode[]
}

const props = defineProps<{
  data: DeviceNode[]
}>()

const defaultProps = {
  children: 'children',
  label: 'name',
}

const treeData = computed(() => props.data)

const iconMap: Record<string, string> = {
  weather_station: 'MostlyCloudy',
  meter: 'Histogram',
  inverter: 'SetUp',
  string: 'Connection',
  combiner_box: 'OfficeBuilding',
}

const iconFor = (type: string) => iconMap[type] || 'SetUp'

const statusType = (status: string) => {
  if (status === 'active') return 'success'
  if (status === 'fault') return 'danger'
  return 'info'
}
</script>

<style scoped>
.device-tree {
  background: transparent;
  color: var(--pv-text-primary);
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tree-icon {
  color: var(--pv-primary);
}

.tree-label {
  font-weight: 600;
}
</style>
