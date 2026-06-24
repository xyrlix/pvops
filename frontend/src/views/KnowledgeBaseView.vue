<template>
  <DashboardLayout>
    <template #breadcrumb>
      <el-icon class="back-icon" :size="22"><Collection /></el-icon>
      <span>知识库</span>
    </template>

    <template #actions>
      <el-button type="primary" :icon="Refresh" @click="loadDocuments" :loading="loading.list">
        刷新
      </el-button>
    </template>

    <el-row :gutter="20">
      <!-- 左侧：上传 + 文档列表 -->
      <el-col :xs="24" :lg="14">
        <PvCard title="📚 知识库文档" subtitle="支持 PDF、Word、TXT 等格式，上传后自动分块并向量化">
          <div class="upload-section">
            <el-upload
              ref="uploadRef"
              drag
              action="#"
              :auto-upload="false"
              :limit="5"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :file-list="fileList"
              accept=".pdf,.doc,.docx,.txt"
            >
              <el-icon :size="40"><Upload /></el-icon>
              <div class="upload-tip">拖拽文件到此处，或 <em>点击上传</em></div>
              <template #tip>
                <div class="upload-hint">支持 PDF / Word / TXT，单个文件建议不超过 10MB</div>
              </template>
            </el-upload>

            <div class="upload-actions">
              <el-select v-model="uploadStationId" placeholder="关联电站（可选）" clearable style="width: 220px">
                <el-option
                  v-for="station in stationStore.stations"
                  :key="station.id"
                  :label="station.name"
                  :value="station.id"
                />
              </el-select>
              <el-button
                type="primary"
                :icon="Upload"
                :disabled="!fileList.length"
                :loading="loading.upload"
                @click="submitUpload"
              >
                开始上传
              </el-button>
            </div>
          </div>

          <el-divider />

          <el-table :data="documents" v-loading="loading.list" style="width: 100%" empty-text="暂无文档">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="filename" label="文件名" min-width="160" show-overflow-tooltip />
            <el-table-column label="关联电站" width="140">
              <template #default="{ row }">
                {{ row.station_id ? getStationName(row.station_id) : '全局' }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <PvTag :type="row.status === 'active' ? 'success' : 'info'">{{ statusText(row.status) }}</PvTag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="上传时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90" fixed="right">
              <template #default="{ row }">
                <el-button link type="danger" :icon="Delete" @click="deleteDoc(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </PvCard>
      </el-col>

      <!-- 右侧：知识库问答 -->
      <el-col :xs="24" :lg="10">
        <PvCard title="💬 知识库问答" subtitle="基于已上传文档进行 RAG 检索问答">
          <div class="ask-section">
            <el-input
              v-model="question"
              type="textarea"
              :rows="3"
              placeholder="例如：逆变器报绝缘阻抗低故障如何处理？"
              maxlength="500"
              show-word-limit
            />
            <div class="ask-actions">
              <el-select v-model="askStationId" placeholder="限定电站（可选）" clearable style="width: 180px">
                <el-option
                  v-for="station in stationStore.stations"
                  :key="station.id"
                  :label="station.name"
                  :value="station.id"
                />
              </el-select>
              <el-button type="primary" :icon="Search" :loading="loading.ask" @click="askKnowledge">
                提问
              </el-button>
            </div>
          </div>

          <div v-if="answer" class="answer-panel">
            <div class="answer-label">回答</div>
            <div class="answer-content">{{ answer }}</div>

            <div v-if="sources.length" class="sources-section">
              <div class="sources-label">参考来源</div>
              <el-collapse>
                <el-collapse-item title="展开查看检索片段" name="sources">
                  <div
                    v-for="(source, idx) in sources"
                    :key="idx"
                    class="source-item"
                  >
                    <div class="source-meta">{{ source.metadata?.filename || '未知文档' }}</div>
                    <div class="source-text">{{ source.content }}</div>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>

          <el-empty v-else description="输入问题后点击提问，即可从知识库获取答案" />
        </PvCard>
      </el-col>
    </el-row>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Collection, Upload, Delete, Search, Refresh } from '@element-plus/icons-vue'
import type { UploadFile, UploadUserFile } from 'element-plus'
import DashboardLayout from '@/components/DashboardLayout.vue'
import PvCard from '@/components/PvCard.vue'
import PvTag from '@/components/PvTag.vue'
import { knowledgeApi } from '@/services/api'
import { useStationStore } from '@/stores/station'
import { ElMessage, ElMessageBox } from 'element-plus'

interface KnowledgeDoc {
  id: number
  filename: string
  station_id?: number | null
  status: string
  created_at: string
}

const stationStore = useStationStore()
const documents = ref<KnowledgeDoc[]>([])
const fileList = ref<UploadUserFile[]>([])
const uploadStationId = ref<number | undefined>(undefined)
const question = ref('')
const askStationId = ref<number | undefined>(undefined)
const answer = ref('')
const sources = ref<any[]>([])
const loading = ref({ list: false, upload: false, ask: false })

const statusText = (status?: string) => (status === 'active' ? '已索引' : status || '未知')

const formatDate = (iso?: string) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

const getStationName = (id?: number | null) => {
  if (!id) return '全局'
  return stationStore.stations.find((s) => s.id === id)?.name || `电站#${id}`
}

const loadDocuments = async () => {
  loading.value.list = true
  try {
    const res = await knowledgeApi.listDocuments() as unknown as KnowledgeDoc[]
    documents.value = Array.isArray(res) ? res : []
  } catch (err) {
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value.list = false
  }
}

const handleFileChange = (_file: UploadFile, files: UploadUserFile[]) => {
  fileList.value = files
}

const handleFileRemove = (_file: UploadFile, files: UploadUserFile[]) => {
  fileList.value = files
}

const submitUpload = async () => {
  if (!fileList.value.length) return
  loading.value.upload = true
  try {
    for (const file of fileList.value) {
      const raw = file.raw
      if (!raw) continue
      await knowledgeApi.uploadDocument(raw, uploadStationId.value)
    }
    ElMessage.success('上传成功')
    fileList.value = []
    await loadDocuments()
  } catch (err) {
    ElMessage.error('上传失败')
  } finally {
    loading.value.upload = false
  }
}

const deleteDoc = async (id: number) => {
  try {
    await ElMessageBox.confirm('删除后不可恢复，是否继续？', '确认删除', { type: 'warning' })
    await knowledgeApi.deleteDocument(id)
    ElMessage.success('删除成功')
    await loadDocuments()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const askKnowledge = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  loading.value.ask = true
  answer.value = ''
  sources.value = []
  try {
    const res = await knowledgeApi.ask(question.value, askStationId.value, 4) as unknown as {
      answer: string
      sources: any[]
    }
    answer.value = res.answer || ''
    sources.value = res.sources || []
  } catch (err) {
    ElMessage.error('问答失败')
  } finally {
    loading.value.ask = false
  }
}

onMounted(() => {
  stationStore.fetchStations()
  loadDocuments()
})
</script>

<style scoped>
.upload-section {
  margin-bottom: 12px;
}

.upload-tip {
  margin-top: 8px;
  color: var(--pv-text-secondary);
  font-size: 14px;
}

.upload-tip em {
  color: var(--pv-primary);
  font-style: normal;
  font-weight: 600;
}

.upload-hint {
  margin-top: 8px;
  color: var(--pv-text-tertiary);
  font-size: 12px;
}

.upload-actions {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.ask-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ask-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.answer-panel {
  margin-top: 20px;
  padding: 16px;
  border-radius: var(--pv-radius-sm);
  background: var(--el-fill-color-light);
}

.answer-label,
.sources-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--pv-text-tertiary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.answer-content {
  color: var(--pv-text-primary);
  line-height: 1.7;
  white-space: pre-wrap;
}

.sources-section {
  margin-top: 16px;
}

.source-item {
  padding: 10px 0;
  border-bottom: 1px dashed var(--pv-border);
}

.source-item:last-child {
  border-bottom: none;
}

.source-meta {
  font-size: 12px;
  color: var(--pv-primary);
  margin-bottom: 4px;
}

.source-text {
  font-size: 13px;
  color: var(--pv-text-secondary);
  line-height: 1.6;
}
</style>
