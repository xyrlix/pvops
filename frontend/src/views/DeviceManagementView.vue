<template>
  <DashboardLayout>
    <template #breadcrumb>
      <el-icon class="back-icon" :size="22"><SetUp /></el-icon>
      <span>设备管理</span>
    </template>

    <template #actions>
      <el-select v-model="selectedStationId" placeholder="选择电站" style="width: 200px" @change="loadData">
        <el-option
          v-for="station in stationStore.stations"
          :key="station.id"
          :label="station.name"
          :value="station.id"
        />
      </el-select>
    </template>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="8">
        <PvCard title="设备拓扑" icon="Grid" glow class="tree-card">
          <DeviceTopologyTree :data="topology" />
        </PvCard>
      </el-col>
      <el-col :xs="24" :lg="16">
        <PvCard title="设备清单" icon="List" glow class="table-card">
          <template #actions>
            <el-radio-group v-model="filterType" size="small" @change="loadDevices">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="inverter">逆变器</el-radio-button>
              <el-radio-button label="weather_station">气象站</el-radio-button>
              <el-radio-button label="meter">关口表</el-radio-button>
              <el-radio-button label="string">组串</el-radio-button>
            </el-radio-group>
          </template>
          <el-table :data="devices" stripe>
            <el-table-column prop="device_code" label="编号" width="130" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="device_type" label="类型" width="120">
              <template #default="{ row }">
                <PvTag :type="'info'" :label="typeLabel(row.device_type)" size="small" />
              </template>
            </el-table-column>
            <el-table-column prop="vendor" label="厂商" />
            <el-table-column prop="model" label="型号" />
            <el-table-column prop="protocol" label="协议" width="110" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <PvTag :type="row.status === 'active' ? 'running' : 'inactive'" :label="row.status === 'active' ? '运行' : '停用'" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button size="small" type="primary" plain @click="showDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </PvCard>
      </el-col>
    </el-row>

    <el-drawer v-model="detailVisible" title="设备详情" size="400px">
      <el-descriptions :column="1" border v-if="selectedDevice">
        <el-descriptions-item label="编号">{{ selectedDevice.device_code }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ selectedDevice.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ typeLabel(selectedDevice.device_type) }}</el-descriptions-item>
        <el-descriptions-item label="厂商">{{ selectedDevice.vendor || '-' }}</el-descriptions-item>
        <el-descriptions-item label="型号">{{ selectedDevice.model || '-' }}</el-descriptions-item>
        <el-descriptions-item label="序列号">{{ selectedDevice.sn || '-' }}</el-descriptions-item>
        <el-descriptions-item label="协议">{{ selectedDevice.protocol || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ selectedDevice.status }}</el-descriptions-item>
      </el-descriptions>
      <div class="config-title">协议配置</div>
      <pre v-if="selectedDevice" class="config-pre">{{ JSON.stringify(selectedDevice.config, null, 2) }}</pre>
    </el-drawer>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { SetUp } from '@element-plus/icons-vue'
import { useStationStore } from '@/stores/station'
import { deviceApi } from '@/services/api'
import DashboardLayout from '@/components/DashboardLayout.vue'
import PvCard from '@/components/PvCard.vue'
import PvTag from '@/components/PvTag.vue'
import DeviceTopologyTree from '@/components/DeviceTopologyTree.vue'

interface DeviceItem {
  id: number
  station_id: number
  parent_id?: number
  device_type: string
  device_code: string
  name: string
  vendor?: string
  model?: string
  sn?: string
  protocol?: string
  config?: Record<string, any>
  status: string
}

const stationStore = useStationStore()
const selectedStationId = ref<number | null>(null)
const filterType = ref('')
const devices = ref<DeviceItem[]>([])
const topology = ref<DeviceItem[]>([])
const detailVisible = ref(false)
const selectedDevice = ref<DeviceItem | null>(null)

const typeLabel = (type: string) => {
  const map: Record<string, string> = {
    inverter: '逆变器',
    weather_station: '气象站',
    meter: '关口表',
    combiner_box: '汇流箱',
    string: '组串',
  }
  return map[type] || type
}

const loadDevices = async () => {
  if (!selectedStationId.value) return
  try {
    const data = (await deviceApi.list(
      selectedStationId.value,
      filterType.value || undefined
    )) as unknown as DeviceItem[]
    devices.value = data
  } catch (err) {
    console.error('加载设备失败:', err)
  }
}

const loadTopology = async () => {
  if (!selectedStationId.value) return
  try {
    const data = (await deviceApi.topology(selectedStationId.value)) as unknown as DeviceItem[]
    topology.value = data
  } catch (err) {
    console.error('加载拓扑失败:', err)
  }
}

const loadData = () => {
  loadDevices()
  loadTopology()
}

const showDetail = (row: DeviceItem) => {
  selectedDevice.value = row
  detailVisible.value = true
}

onMounted(() => {
  stationStore.fetchStations().then(() => {
    const demo = stationStore.stations.find((s) => s.code === 'DEMO-001')
    selectedStationId.value = demo?.id || stationStore.stations[0]?.id || null
    if (selectedStationId.value) loadData()
  })
})
</script>

<style scoped>
.tree-card {
  min-height: 600px;
}

.table-card {
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
  font-size: 16px;
  color: var(--pv-text-primary);
}

.config-title {
  margin-top: 20px;
  margin-bottom: 10px;
  font-weight: 700;
  color: var(--pv-text-primary);
}

.config-pre {
  background: rgba(0, 0, 0, 0.25);
  padding: 14px;
  border-radius: 10px;
  color: var(--pv-text-secondary);
  overflow: auto;
}
</style>
