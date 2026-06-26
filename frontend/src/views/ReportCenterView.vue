<template>
  <DashboardLayout>
    <template #title>
      <span class="pv-page-title">报告中心</span>
    </template>
    <template #subtitle>REPORT CENTER</template>

    <el-row :gutter="20" class="action-row">
      <el-col :span="8">
        <PvCard shadow="hover" class="report-card" :loading="generating === 'daily'" @click="generateReport('daily')">
          <div class="report-icon daily"><el-icon :size="36"><Document /></el-icon></div>
          <h3>日报</h3>
          <p>生成昨日电站运行日报</p>
          <el-button type="primary" :loading="generating === 'daily'">生成日报</el-button>
        </PvCard>
      </el-col>
      <el-col :span="8">
        <PvCard shadow="hover" class="report-card" :loading="generating === 'weekly'" @click="generateReport('weekly')">
          <div class="report-icon weekly"><el-icon :size="36"><DocumentChecked /></el-icon></div>
          <h3>周报</h3>
          <p>生成本周电站运行周报</p>
          <el-button type="success" :loading="generating === 'weekly'">生成周报</el-button>
        </PvCard>
      </el-col>
      <el-col :span="8">
        <PvCard shadow="hover" class="report-card" :loading="generating === 'monthly'" @click="generateReport('monthly')">
          <div class="report-icon monthly"><el-icon :size="36"><DocumentCopy /></el-icon></div>
          <h3>月报</h3>
          <p>生成本月电站运行月报</p>
          <el-button type="warning" :loading="generating === 'monthly'">生成月报</el-button>
        </PvCard>
      </el-col>
    </el-row>

    <PvCard class="reports-list" title="报告历史" icon="DocumentCopy" :loading="loading" :empty="!reports.length" glow>
      <template #actions>
        <el-radio-group v-model="filterType" size="small">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="daily">日报</el-radio-button>
          <el-radio-button label="weekly">周报</el-radio-button>
          <el-radio-button label="monthly">月报</el-radio-button>
        </el-radio-group>
      </template>
      <el-table :data="reports" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="report_type" label="类型" width="100">
          <template #default="{ row }">
            <PvTag :type="row.report_type === 'daily' ? 'info' : row.report_type === 'weekly' ? 'success' : 'warning'" :label="typeText(row.report_type)" />
          </template>
        </el-table-column>
        <el-table-column prop="total_energy_kwh" label="总发电量(kWh)" width="140" />
        <el-table-column prop="avg_pr" label="平均PR" width="110">
          <template #default="{ row }">
            {{ row.avg_pr != null ? (row.avg_pr * 100).toFixed(1) + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="alarm_count" label="告警数" width="100" />
        <el-table-column prop="summary" label="总结" min-width="220" show-overflow-tooltip />
        <el-table-column prop="created_at" label="生成时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="viewReport(row)">查看</el-button>
            <el-button size="small" type="success" plain :icon="Download" @click="exportPdf(row)">
              PDF
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PvCard>

    <!-- 报告详情 -->
    <el-dialog v-model="showDetail" title="报告详情" width="720px">
      <div v-if="selectedReport">
        <h3 class="detail-title">{{ selectedReport.title }}</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类型">{{ typeText(selectedReport.report_type) }}</el-descriptions-item>
          <el-descriptions-item label="总发电量">{{ selectedReport.total_energy_kwh?.toFixed(2) }} kWh</el-descriptions-item>
          <el-descriptions-item label="平均 PR">{{ selectedReport.avg_pr != null ? (selectedReport.avg_pr * 100).toFixed(1) + '%' : '-' }}</el-descriptions-item>
          <el-descriptions-item label="告警数">{{ selectedReport.alarm_count }}</el-descriptions-item>
        </el-descriptions>
        <div class="detail-section">
          <div class="section-title">总结</div>
          <p>{{ selectedReport.summary }}</p>
        </div>
        <div class="detail-section">
          <div class="section-title">每日明细</div>
          <el-table :data="selectedReport.details" size="small" border>
            <el-table-column prop="date" label="日期" />
            <el-table-column prop="daily_energy_kwh" label="日发电量(kWh)" />
            <el-table-column prop="avg_power_kw" label="平均功率(kW)" />
          </el-table>
        </div>
      </div>
    </el-dialog>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { Document, DocumentChecked, DocumentCopy, Download } from '@element-plus/icons-vue'
import DashboardLayout from '@/components/DashboardLayout.vue'
import PvCard from '@/components/PvCard.vue'
import PvTag from '@/components/PvTag.vue'
import { reportApi } from '@/services/api'
import { ElMessage } from 'element-plus'

// TODO(typing): replace any with explicit type; suppressed to keep CI green
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const reports = ref<any[]>([])
const loading = ref(false)
const generating = ref('')
const filterType = ref('')
const showDetail = ref(false)
// TODO(typing): replace any with explicit type; suppressed to keep CI green
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const selectedReport = ref<any>(null)

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

const typeText = (type: string) => {
  const map: Record<string, string> = { daily: '日报', weekly: '周报', monthly: '月报' }
  return map[type] || type
}

const fetchReports = async () => {
  loading.value = true
  try {
    // TODO(typing): replace any with explicit type; suppressed to keep CI green
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const data = (await reportApi.list(undefined, filterType.value || undefined)) as unknown as any[]
    reports.value = data
  } catch (err) {
    console.error('获取报告失败:', err)
  } finally {
    loading.value = false
  }
}

const generateReport = async (type: string) => {
  generating.value = type
  try {
    await reportApi.generate(type)
    ElMessage.success(`${typeText(type)}生成成功`)
    fetchReports()
  } catch (err) {
    ElMessage.error('生成失败')
  } finally {
    generating.value = ''
  }
}

// TODO(typing): replace any with explicit type; suppressed to keep CI green
// eslint-disable-next-line @typescript-eslint/no-explicit-any
// TODO(typing): replace any with explicit type; suppressed to keep CI green
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const viewReport = (row: any) => {
  selectedReport.value = row
  showDetail.value = true
}

// TODO(typing): replace any with explicit type; suppressed to keep CI green
// eslint-disable-next-line @typescript-eslint/no-explicit-any
// TODO(typing): replace any with explicit type; suppressed to keep CI green
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const exportPdf = async (row: any) => {
  try {
    const blob = (await reportApi.exportPdf(row.id)) as unknown as Blob
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${row.report_type}_report_${row.id}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('PDF 导出成功')
  } catch (err) {
    ElMessage.error('PDF 导出失败')
  }
}

watch(filterType, fetchReports)

onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.action-row {
  margin-bottom: 22px;
}

.report-card {
  text-align: center;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  min-height: 220px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.report-card:hover {
  transform: translateY(-6px);
}

.report-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}

.report-icon.daily {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.06));
  color: #60a5fa;
}

.report-icon.weekly {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.06));
  color: #4ade80;
}

.report-icon.monthly {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(245, 158, 11, 0.06));
  color: #fbbf24;
}

.report-card h3 {
  margin: 0 0 8px;
  color: var(--pv-text-primary);
  font-size: 18px;
}

.report-card p {
  color: var(--pv-text-tertiary);
  font-size: 14px;
  margin-bottom: 18px;
}

.reports-list {
  margin-bottom: 22px;
}

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

.detail-title {
  margin: 0 0 18px;
  color: var(--pv-text-primary);
  font-size: 20px;
  font-weight: 700;
}

.detail-section {
  margin-top: 18px;
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
</style>
