<template>
  <DashboardLayout>
    <template #title>
      <el-icon :size="18" @click="$router.back()" style="cursor:pointer;margin-right:6px"><ArrowLeft /></el-icon>
      <span class="pv-page-title">AI 诊断报告</span>
    </template>
    <template #subtitle>DIAGNOSIS REPORT</template>

    <!-- 报告头部 -->
    <PvCard v-if="report" class="report-header" glow>
      <div class="report-title">
        <h2>{{ report.station_name || `电站 ${report.station_id}` }} 诊断报告</h2>
        <PvTag :type="healthTagType" :label="`健康度 ${report.overall_health?.toFixed(1)} 分`" size="large" />
      </div>
      <div class="report-meta">
        <span><el-icon><Clock /></el-icon>诊断时间：{{ formatTime(report.diagnosis_time || report.created_at) }}</span>
        <span><el-icon><Warning /></el-icon>发现异常：{{ report.findings?.length || 0 }} 项</span>
        <span><el-icon><Document /></el-icon>报告类型：AI 智能诊断</span>
      </div>
      <div class="report-summary">
        <el-alert :title="report.summary" :type="healthAlertType" :closable="false" show-icon />
      </div>
      <div class="report-actions">
        <el-button type="primary" @click="exportPdf">
          <el-icon><Download /></el-icon> 导出 PDF
        </el-button>
        <el-button type="info" plain @click="askAiAboutReport">
          <el-icon><ChatDotRound /></el-icon> 询问 AI
        </el-button>
      </div>
    </PvCard>

    <!-- 建议列表 -->
    <PvCard v-if="report && report.suggestions?.length" title="处理建议" icon="List" class="suggestions-card" glow>
      <el-steps direction="vertical" :active="1">
        <el-step
          v-for="(suggestion, index) in report.suggestions"
          :key="index"
          :title="suggestion"
        />
      </el-steps>
    </PvCard>

    <!-- 异常发现 -->
    <PvCard v-if="report && report.findings?.length" title="异常发现" icon="Warning" class="findings-card" glow>
      <div
        v-for="finding in report.findings"
        :key="finding.title"
        class="finding-item"
        :class="finding.severity"
      >
        <div class="finding-header">
          <PvTag :type="finding.severity === 'critical' ? 'urgent' : 'high'" :label="finding.severity === 'critical' ? '严重' : '警告'" size="large" />
          <span class="finding-category">{{ finding.category }}</span>
          <h4>{{ finding.title }}</h4>
        </div>
        <p class="finding-desc">{{ finding.description }}</p>

        <div class="finding-section">
          <div class="section-title">证据链</div>
          <ul>
            <li v-for="evidence in finding.evidence" :key="evidence">{{ evidence }}</li>
          </ul>
        </div>

        <div class="finding-section">
          <div class="section-title">根因分析</div>
          <p>{{ finding.root_cause }}</p>
        </div>

        <div class="finding-section">
          <div class="section-title">处理建议</div>
          <ol>
            <li v-for="suggestion in finding.suggestions" :key="suggestion">{{ suggestion }}</li>
          </ol>
        </div>
      </div>
    </PvCard>

    <!-- 无异常 -->
    <PvCard v-else-if="report && !report.findings?.length" title="运行正常" icon="CircleCheck" class="findings-card" glow>
      <el-result icon="success" title="运行正常" :sub-title="report.summary" />
    </PvCard>

    <!-- 反馈 -->
    <PvCard v-if="report" title="诊断反馈" icon="Warning" class="feedback-card" glow>
      <div v-if="!feedbackSubmitted">
        <p class="feedback-desc">这份报告对您有帮助吗？您的反馈将帮助我们改进 AI 诊断能力。</p>
        <el-radio-group v-model="feedbackRating" class="feedback-rating">
          <el-radio-button label="good">完全正确</el-radio-button>
          <el-radio-button label="partial">部分正确</el-radio-button>
          <el-radio-button label="bad">不正确</el-radio-button>
        </el-radio-group>
        <el-input
          v-model="feedbackComment"
          type="textarea"
          :rows="2"
          placeholder="补充说明（可选）"
          class="feedback-comment"
        />
        <el-button type="primary" :disabled="!feedbackRating" @click="submitFeedback">
          提交反馈
        </el-button>
      </div>
      <el-result v-else icon="success" title="反馈已提交" sub-title="感谢您的反馈" />
    </PvCard>

    <!-- 生成中 -->
    <PvLoading v-else-if="loading" text="AI 正在分析电站运行数据，请稍候..." />
  </DashboardLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Warning, Clock, Document, Download, ChatDotRound } from '@element-plus/icons-vue'
import { diagnosisApi } from '@/services/api'
import DashboardLayout from '@/components/DashboardLayout.vue'
import PvCard from '@/components/PvCard.vue'
import PvTag from '@/components/PvTag.vue'
import PvLoading from '@/components/PvLoading.vue'
import { useCopilotStore } from '@/stores/copilot'
import { ElMessage } from 'element-plus'

const route = useRoute()
const copilotStore = useCopilotStore()
const report = ref<any>(null)
const loading = ref(true)
const feedbackRating = ref('')
const feedbackComment = ref('')
const feedbackSubmitted = ref(false)

const healthTagType = computed(() => {
  const score = report.value?.overall_health || 100
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
})

const healthAlertType = computed(() => {
  const score = report.value?.overall_health || 100
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'error'
})

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

const exportPdf = async () => {
  if (!report.value) return
  try {
    const res = (await diagnosisApi.exportReportPdf(report.value.id)) as unknown as Blob
    const url = window.URL.createObjectURL(res)
    const link = document.createElement('a')
    link.href = url
    link.download = `diagnosis_report_${report.value.id}.pdf`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('PDF 导出成功')
  } catch (err) {
    ElMessage.error('PDF 导出失败，请确认后端已安装 reportlab')
    console.error(err)
  }
}

const askAiAboutReport = () => {
  copilotStore.open({
    type: 'diagnosis',
    diagnosis_report_id: report.value?.id,
    station_id: report.value?.station_id,
  })
}

const submitFeedback = async () => {
  if (!report.value || !feedbackRating.value) return
  try {
    await diagnosisApi.createFeedback(report.value.id, {
      rating: feedbackRating.value,
      comment: feedbackComment.value,
    })
    feedbackSubmitted.value = true
    ElMessage.success('反馈已提交')
  } catch (err) {
    ElMessage.error('提交反馈失败')
    console.error(err)
  }
}

onMounted(async () => {
  try {
    const stationId = Number(route.params.id)
    const data = (await diagnosisApi.diagnoseStation(stationId)) as unknown as any
    report.value = data
  } catch (err) {
    ElMessage.error('生成诊断报告失败')
    console.error(err)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.report-header {
  margin-bottom: 22px;
}

.report-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.report-title h2 {
  margin: 0;
  color: var(--pv-text-primary);
  font-weight: 800;
  font-size: 24px;
}

.report-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  color: var(--pv-text-secondary);
  font-size: 14px;
  margin-bottom: 18px;
}

.report-meta span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.report-summary {
  margin-top: 16px;
}

.report-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

.suggestions-card {
  margin-bottom: 22px;
}

.findings-card {
  margin-bottom: 22px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 16px;
  color: var(--pv-text-primary);
}

.finding-item {
  padding: 20px;
  margin-bottom: 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--pv-border);
  border-left: 4px solid #f59e0b;
}

.finding-item.critical {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.finding-item:last-child {
  margin-bottom: 0;
}

.finding-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.finding-header h4 {
  margin: 0;
  color: var(--pv-text-primary);
  font-size: 17px;
}

.finding-category {
  color: var(--pv-text-tertiary);
  font-size: 13px;
}

.finding-desc {
  color: var(--pv-text-secondary);
  margin-bottom: 18px;
  line-height: 1.6;
}

.finding-section {
  margin-bottom: 14px;
}

.section-title {
  font-weight: 700;
  color: var(--pv-text-primary);
  margin-bottom: 10px;
  font-size: 14px;
}

.finding-section ul,
.finding-section ol {
  margin: 0;
  padding-left: 20px;
  color: var(--pv-text-secondary);
}

.finding-section li {
  margin-bottom: 6px;
}

.feedback-card {
  margin-bottom: 22px;
}

.feedback-desc {
  color: var(--pv-text-secondary);
  margin-bottom: 14px;
}

.feedback-rating {
  margin-bottom: 14px;
}

.feedback-comment {
  margin-bottom: 14px;
}

.generating-card {
  text-align: center;
}

.generating {
  padding: 80px 20px;
  color: var(--pv-text-secondary);
}

.generating p {
  margin-top: 18px;
  font-size: 15px;
}
</style>
