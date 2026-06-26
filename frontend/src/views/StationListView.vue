<template>
  <DashboardLayout>
    <template #title>
      <span class="pv-page-title">电站管理</span>
    </template>
    <template #subtitle>STATION REGISTRY · {{ stationStore.stations.length }} UNITS</template>

    <PvCard title="电站列表" icon="OfficeBuilding" :loading="stationStore.loading" glow>
      <template #actions>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>新增电站
        </el-button>
      </template>

      <el-table :data="stationStore.stations" stripe style="width: 100%">
        <el-table-column prop="name" label="电站名称" min-width="160" />
        <el-table-column prop="code" label="电站编码" min-width="130" />
        <el-table-column prop="capacity_kw" label="装机容量(kW)" min-width="140" />
        <el-table-column prop="location" label="位置" min-width="200" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <PvTag :type="row.status === 'active' ? 'running' : 'inactive'" :label="row.status === 'active' ? '运行中' : '停用'" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="viewDetail(row.id)">详情</el-button>
            <el-button size="small" type="danger" plain @click="deleteStation(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </PvCard>

    <!-- 新增电站对话框 -->
    <el-dialog v-model="showCreateDialog" title="新增电站" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="电站名称">
          <el-input v-model="form.name" placeholder="请输入电站名称" />
        </el-form-item>
        <el-form-item label="电站编码">
          <el-input v-model="form.code" placeholder="请输入电站编码" />
        </el-form-item>
        <el-form-item label="装机容量">
          <el-input-number v-model="form.capacity_kw" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" placeholder="请输入电站位置" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createStation">确定</el-button>
      </template>
    </el-dialog>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { useStationStore } from '@/stores/station'
import { stationApi } from '@/services/api'
import DashboardLayout from '@/components/DashboardLayout.vue'
import PvCard from '@/components/PvCard.vue'
import PvTag from '@/components/PvTag.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const stationStore = useStationStore()

const showCreateDialog = ref(false)
const form = reactive({
  name: '',
  code: '',
  capacity_kw: 100,
  location: '',
})

onMounted(() => {
  stationStore.fetchStations()
})

const viewDetail = (id: number) => {
  router.push(`/stations/${id}`)
}

const createStation = async () => {
  try {
    await stationApi.create(form)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    stationStore.fetchStations()
  } catch (err) {
    ElMessage.error('创建失败')
    console.error(err)
  }
}

const deleteStation = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除该电站吗？', '提示', { type: 'warning' })
    await stationApi.delete(id)
    ElMessage.success('删除成功')
    stationStore.fetchStations()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(err)
    }
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 16px;
  color: var(--pv-text-primary);
}
</style>
