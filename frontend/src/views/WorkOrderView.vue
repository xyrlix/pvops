<template>
  <DashboardLayout>
    <template #title>
      <span class="pv-page-title">工单管理</span>
    </template>
    <template #subtitle>WORK ORDER</template>

    <template #actions>
      <el-button type="primary" @click="showCreate = true">
        <el-icon><Plus /></el-icon> 新建工单
      </el-button>
    </template>

    <!-- KPI -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card pending">
          <div class="stat-value">
            <PvSkeleton v-if="statsLoading" variant="text" :rows="1" />
            <template v-else>{{ pendingCount }}</template>
          </div>
          <div class="stat-label">待处理</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card inprogress">
          <div class="stat-value">
            <PvSkeleton v-if="statsLoading" variant="text" :rows="1" />
            <template v-else>{{ inProgressCount }}</template>
          </div>
          <div class="stat-label">处理中</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card completed">
          <div class="stat-value">
            <PvSkeleton v-if="statsLoading" variant="text" :rows="1" />
            <template v-else>{{ completedCount }}</template>
          </div>
          <div class="stat-label">已完成</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card rate">
          <div class="stat-value">
            <PvSkeleton v-if="statsLoading" variant="text" :rows="1" />
            <template v-else>{{ completionRate }}%</template>
          </div>
          <div class="stat-label">本周完成率</div>
        </div>
      </el-col>
    </el-row>

    <!-- 工单列表 -->
    <el-row class="list-row">
      <el-col :span="24">
        <PvCard title="工单列表" icon="Tickets" glow :loading="statsLoading">
          <el-table :data="workOrders" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="title" label="标题" min-width="180" />
            <el-table-column prop="priority" label="优先级" width="90">
              <template #default="{ row }">
                <PvTag :type="row.priority" :label="priorityText(row.priority)" />
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <PvTag :type="row.status === 'pending' ? 'danger' : row.status === 'in_progress' ? 'warning' : 'success'" :label="statusText(row.status)" />
              </template>
            </el-table-column>
            <el-table-column prop="assignee" label="负责人" width="130" />
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" plain @click="viewDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </PvCard>
      </el-col>
    </el-row>

    <!-- 新建工单 -->
    <el-dialog v-model="showCreate" title="新建工单" width="520px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="请输入工单标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请描述问题" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" style="width: 100%">
            <el-option label="紧急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="form.assignee" placeholder="请输入负责人" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createWorkOrder">确定</el-button>
      </template>
    </el-dialog>

    <!-- 工单详情 -->
    <el-dialog v-model="showDetail" title="工单详情" width="680px">
      <div v-if="selectedOrder">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题">{{ selectedOrder.title }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <PvTag :type="selectedOrder.status === 'pending' ? 'danger' : selectedOrder.status === 'in_progress' ? 'warning' : 'success'" :label="statusText(selectedOrder.status)" />
          </el-descriptions-item>
          <el-descriptions-item label="优先级">
            <PvTag :type="selectedOrder.priority" :label="priorityText(selectedOrder.priority)" />
          </el-descriptions-item>
          <el-descriptions-item label="负责人">{{ selectedOrder.assignee || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div class="detail-section">
          <div class="section-title">问题描述</div>
          <p>{{ selectedOrder.description || '无' }}</p>
        </div>

        <div v-if="selectedOrder.status !== 'completed'" class="detail-section">
          <div class="section-title">处理反馈</div>
          <el-input
            v-model="feedbackForm.comment"
            type="textarea"
            rows="2"
            placeholder="输入处理反馈"
          />
        </div>

        <div v-if="selectedOrder.status === 'in_progress' || selectedOrder.status === 'completed'" class="detail-section">
          <div class="section-title">解决方案</div>
          <el-input
            v-model="feedbackForm.solution"
            type="textarea"
            rows="3"
            placeholder="请输入解决方案（完成工单时必填）"
          />
        </div>

        <div class="detail-actions">
          <el-button
            v-if="selectedOrder.status === 'pending'"
            type="primary"
            @click="updateStatus('in_progress')"
          >开始处理</el-button>
          <el-button
            v-if="selectedOrder.status !== 'completed'"
            type="success"
            @click="updateStatus('completed')"
          >完成工单</el-button>
          <el-button
            v-if="selectedOrder.status === 'completed'"
            type="warning"
            plain
            @click="archiveCase"
          >沉淀为案例</el-button>
        </div>

        <div class="detail-section">
          <div class="section-title">处理时间线</div>
          <WorkOrderTimeline :timeline="timeline" />
        </div>
      </div>
    </el-dialog>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import DashboardLayout from '@/components/DashboardLayout.vue'
import PvCard from '@/components/PvCard.vue'
import PvTag from '@/components/PvTag.vue'
import PvSkeleton from '@/components/PvSkeleton.vue'
import WorkOrderTimeline from '@/components/WorkOrderTimeline.vue'
import { workOrderApi } from '@/services/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const workOrders = ref<any[]>([])
const loading = ref(false)
const statsLoading = ref(false)
const showCreate = ref(false)
const showDetail = ref(false)
const selectedOrder = ref<any>(null)
const timeline = ref<any[]>([])

const form = ref({
  title: (route.query.title as string) || '',
  description: (route.query.description as string) || '',
  priority: 'medium',
  assignee: '',
  alarm_id: route.query.alarm_id ? Number(route.query.alarm_id) : undefined,
  station_id: route.query.station_id ? Number(route.query.station_id) : undefined,
})

const feedbackForm = ref({
  comment: '',
  solution: '',
})

const pendingCount = computed(() => workOrders.value.filter((o) => o.status === 'pending').length)
const inProgressCount = computed(() => workOrders.value.filter((o) => o.status === 'in_progress').length)
const completedCount = computed(() => workOrders.value.filter((o) => o.status === 'completed').length)
const completionRate = computed(() => {
  const total = workOrders.value.length
  return total ? Math.round((completedCount.value / total) * 100) : 0
})

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

const priorityText = (p: string) => {
  const map: Record<string, string> = { urgent: '紧急', high: '高', medium: '中', low: '低' }
  return map[p] || p
}

const statusText = (s: string) => {
  const map: Record<string, string> = { pending: '待处理', in_progress: '处理中', completed: '已完成' }
  return map[s] || s
}

const fetchWorkOrders = async () => {
  loading.value = true
  statsLoading.value = true
  try {
    const data = (await workOrderApi.list()) as unknown as any[]
    workOrders.value = data
  } catch (err) {
    console.error('获取工单失败:', err)
  } finally {
    loading.value = false
    statsLoading.value = false
  }
}

const createWorkOrder = async () => {
  try {
    await workOrderApi.create(form.value)
    ElMessage.success('工单创建成功')
    showCreate.value = false
    fetchWorkOrders()
  } catch (err) {
    ElMessage.error('创建失败')
  }
}

const viewDetail = async (row: any) => {
  selectedOrder.value = row
  feedbackForm.value = { comment: '', solution: '' }
  showDetail.value = true
  try {
    const data = await workOrderApi.timeline(row.id)
    timeline.value = data as unknown as any[]
  } catch {
    timeline.value = []
  }
}

const updateStatus = async (status: string) => {
  if (!selectedOrder.value) return
  if (status === 'completed' && !feedbackForm.value.solution) {
    ElMessage.warning('请填写解决方案')
    return
  }
  try {
    await workOrderApi.updateStatus(selectedOrder.value.id, status, feedbackForm.value.comment, feedbackForm.value.solution)
    ElMessage.success('状态更新成功')
    showDetail.value = false
    fetchWorkOrders()
  } catch (err) {
    ElMessage.error('更新失败')
  }
}

const archiveCase = async () => {
  if (!selectedOrder.value) return
  try {
    const res: any = await workOrderApi.archiveCase(selectedOrder.value.id)
    ElMessage.success(`已沉淀为知识库案例 #${res.knowledge_doc_id}`)
  } catch {
    ElMessage.error('沉淀失败')
  }
}

onMounted(() => {
  fetchWorkOrders()
})
</script>

<style scoped>
.stats-row {
  margin-bottom: 22px;
}

.stat-card {
  padding: 18px;
  border-radius: 14px;
  background: var(--pv-surface);
  border: 1px solid var(--pv-border);
  text-align: center;
  position: relative;
  overflow: hidden;
  transition: var(--pv-transition);
}

.stat-card:hover {
  transform: translateY(-3px);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.stat-card.pending::before { background: var(--pv-danger); box-shadow: 0 0 12px var(--pv-danger); }
.stat-card.inprogress::before { background: var(--pv-warning); box-shadow: 0 0 12px var(--pv-warning); }
.stat-card.completed::before { background: var(--pv-success); box-shadow: 0 0 12px var(--pv-success); }
.stat-card.rate::before { background: var(--pv-primary); box-shadow: 0 0 12px var(--pv-primary); }

.stat-value {
  font-size: 30px;
  font-weight: 900;
  font-family: var(--pv-font-display);
  color: var(--pv-text-primary);
  margin-bottom: 6px;
}

.stat-label {
  font-size: 13px;
  color: var(--pv-text-secondary);
}

.list-row {
  margin-bottom: 22px;
}

.detail-section {
  margin: 18px 0;
}

.section-title {
  font-weight: 700;
  margin-bottom: 10px;
  color: var(--pv-text-primary);
}

.detail-section p {
  color: var(--pv-text-secondary);
  line-height: 1.6;
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin: 18px 0;
}
</style>
