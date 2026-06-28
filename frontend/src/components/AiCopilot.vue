<template>
  <div class="ai-copilot">
    <div class="ai-float-btn" @click="copilotStore.toggle">
      <el-icon :size="28"><ChatDotRound /></el-icon>
    </div>

    <el-drawer
      v-model="copilotStore.isOpen"
      title="AI 智能体"
      direction="rtl"
      size="420px"
      :with-header="true"
      class="copilot-drawer"
    >
      <div class="chat-container">
        <div ref="messagesRef" class="chat-messages">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="message"
            :class="msg.role"
          >
            <div class="message-bubble">
              <div class="message-role">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
              <div class="message-content">{{ msg.content }}</div>
              <!-- ThoughtTrace: 推理链展开 -->
              <div v-if="msg.tool_calls?.length" class="thought-trace">
                <div class="trace-toggle" @click="msg._traceOpen = !msg._traceOpen">
                  <el-icon :size="14">
                    <ArrowRight v-if="!msg._traceOpen" />
                    <ArrowDown v-else />
                  </el-icon>
                  <span>Agent 推理轨迹（{{ msg.tool_calls.length }} 步）</span>
                </div>
                <div v-if="msg._traceOpen" class="trace-steps">
                  <div v-for="(tc, tIdx) in msg.tool_calls" :key="tIdx" class="trace-step">
                    <div class="trace-call">
                      <el-icon :size="12"><Aim /></el-icon>
                      <span>调用工具：<code>{{ tc.tool }}</code></span>
                    </div>
                    <div class="trace-input">
                      输入：<code>{{ JSON.stringify(tc.input, null, 1) }}</code>
                    </div>
                    <div v-if="tc.error" class="trace-error">错误：{{ tc.error }}</div>
                    <div v-else class="trace-output">
                      返回：<code>{{ truncate(JSON.stringify(tc.output), 200) }}</code>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="msg.role === 'assistant' && !msg._feedback" class="message-feedback">
                <el-button text size="small" @click="submitFeedback(index, 'good')">
                  <el-icon :size="14"><CircleCheck /></el-icon>
                </el-button>
                <el-button text size="small" @click="submitFeedback(index, 'bad')">
                  <el-icon :size="14"><CircleClose /></el-icon>
                </el-button>
              </div>
              <div v-if="msg.sources && msg.sources.length" class="message-sources">
                <div class="sources-title">参考来源：</div>
                <div
                  v-for="(src, sidx) in msg.sources.slice(0, 2)"
                  :key="sidx"
                  class="source-item"
                >
                  {{ src.metadata?.filename || '知识库' }}：{{ src.content?.slice(0, 60) }}...
                </div>
              </div>
            </div>
          </div>
          <div v-if="loading" class="message assistant">
            <div class="message-bubble">
              <div class="message-role">AI</div>
              <div class="message-content">
                <span class="typing">思考中</span>
              </div>
            </div>
          </div>
        </div>

        <div class="quick-questions">
          <el-tag
            v-for="q in quickQuestions"
            :key="q"
            size="small"
            effect="dark"
            class="quick-tag"
            @click="sendMessage(q)"
          >
            {{ q }}
          </el-tag>
        </div>

        <div class="chat-input-area">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="2"
            placeholder="输入问题，例如：这台逆变器为什么健康度低？"
            @keydown.enter.prevent="sendMessage(inputMessage)"
          />
          <el-button type="primary" :disabled="!inputMessage.trim() || loading" @click="sendMessage(inputMessage)">
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { ChatDotRound, Promotion, Aim, ArrowRight, ArrowDown, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { chatApi } from '@/services/api'
import { useCopilotStore } from '@/stores/copilot'

interface ToolCall {
  tool: string
  input: Record<string, unknown>
  output?: unknown
  error?: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  // TODO(typing): replace any with explicit type; suppressed to keep CI green
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  sources?: any[]
  tool_calls?: ToolCall[]
  _traceOpen?: boolean
  _feedback?: 'good' | 'bad'
}

const copilotStore = useCopilotStore()
const inputMessage = ref('')
const messages = ref<ChatMessage[]>([
  {
    role: 'assistant',
    content: '你好，我是 PVOps AI 运维助手。你可以询问设备状态、告警原因、诊断建议，或基于知识库查询 SOP。',
  },
])
const loading = ref(false)
const sessionId = ref('')
const messagesRef = ref<HTMLElement>()

const quickQuestions = computed(() => {
  const ctx = copilotStore.context
  const type = ctx?.type
  const base = [
    '当前电站健康度如何？',
    'INV001 最近有什么异常？',
    '组串离散率过高怎么处理？',
    '查看相似案例',
  ]
  if (type === 'alarm') {
    return [`诊断这条告警：${ctx?.alarm_title || ''}`, '这条告警可能是什么原因？', '查看相似案例']
  }
  if (type === 'device') {
    return ['立即诊断该电站/设备', '该设备健康度如何？', '查看相似案例']
  }
  if (type === 'station' || type === 'overview') {
    return ['当前电站整体运行如何？', '有哪些潜在风险？', '查看相似案例']
  }
  return base
})

const truncate = (val: unknown, max = 200) => {
  const s = typeof val === 'string' ? val : JSON.stringify(val)
  return s.length > max ? s.slice(0, max) + '...' : s
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

watch(messages, scrollToBottom, { deep: true })

const sendMessage = async (text: string) => {
  if (!text.trim() || loading.value) return
  messages.value.push({ role: 'user', content: text })
  inputMessage.value = ''
  loading.value = true

  try {
    const res = (await chatApi.send({
      message: text,
      session_id: sessionId.value || undefined,
      context: copilotStore.context,
    // TODO(typing): replace any with explicit type; suppressed to keep CI green
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    })) as unknown as { session_id: string; answer: string; tool_calls?: ToolCall[]; sources?: any[] }

    sessionId.value = res.session_id
    messages.value.push({
      role: 'assistant',
      content: res.answer,
      tool_calls: res.tool_calls,
      sources: res.sources,
      _traceOpen: (res.tool_calls?.length ?? 0) > 0,
    })
    // 保存到 localStorage 供 /agent 页面展示历史
    try {
      const history = JSON.parse(localStorage.getItem('pvops-chat-history') || '[]')
      history.unshift({ question: text, answer: res.answer, time: new Date().toISOString() })
      localStorage.setItem('pvops-chat-history', JSON.stringify(history.slice(0, 50)))
    } catch { /* ignore */ }
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: '请求失败，请稍后重试或检查 LLM 配置。',
    })
  } finally {
    loading.value = false
  }
}

const submitFeedback = (index: number, rating: 'good' | 'bad') => {
  const msg = messages.value[index]
  if (!msg || msg._feedback) return
  msg._feedback = rating
  // 反馈写入 API（静默，不阻塞）
  fetch('/api/v1/kb/feedback', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
    },
    body: JSON.stringify({
      question: messages.value[index - 1]?.content || '',
      answer: msg.content,
      rating,
    }),
  }).catch(() => {})
}
</script>

<style scoped>
.ai-copilot {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 1000;
}

.ai-float-btn {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #00f0ff, #bd34fe);
  color: #fff;
  cursor: pointer;
  box-shadow: 0 0 24px rgba(0, 240, 255, 0.45);
  animation: float-pulse 2.5s ease-in-out infinite;
  transition: transform 0.2s;
}

.ai-float-btn:hover {
  transform: scale(1.1);
}

@keyframes float-pulse {
  0%, 100% { box-shadow: 0 0 24px rgba(0, 240, 255, 0.45); }
  50% { box-shadow: 0 0 40px rgba(0, 240, 255, 0.75); }
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message {
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message-bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--pv-border);
  color: var(--pv-text-primary);
}

.message.user .message-bubble {
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.18), rgba(189, 52, 254, 0.12));
  border-color: rgba(0, 240, 255, 0.25);
}

.message-role {
  font-size: 12px;
  font-weight: 700;
  color: var(--pv-primary);
  margin-bottom: 6px;
}

.message-content {
  white-space: pre-wrap;
  line-height: 1.5;
  font-size: 14px;
}

.message-feedback {
  margin-top: 8px;
  display: flex;
  gap: 4px;
  justify-content: flex-end;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 6px;
}

.message-feedback :deep(.el-button) {
  color: var(--pv-text-tertiary);
}
.message-feedback :deep(.el-button:hover) {
  color: var(--pv-primary);
}

.message-sources {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 12px;
  color: var(--pv-text-tertiary);
}

.sources-title {
  font-weight: 700;
  margin-bottom: 4px;
}

.source-item {
  margin-bottom: 4px;
}

.thought-trace {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(96, 165, 250, 0.2);
  font-size: 12px;
}

.trace-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: var(--pv-primary);
  font-weight: 600;
  font-size: 12px;
}

.trace-toggle:hover {
  opacity: 0.8;
}

.trace-steps {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.trace-step {
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(96, 165, 250, 0.06);
  border: 1px solid rgba(96, 165, 250, 0.12);
}

.trace-call {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  color: var(--pv-accent);
  font-size: 11px;
  margin-bottom: 4px;
}

.trace-call code {
  font-family: var(--pv-font-mono);
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
  padding: 1px 6px;
  font-size: 11px;
}

.trace-input,
.trace-output {
  font-family: var(--pv-font-mono);
  font-size: 10px;
  color: var(--pv-text-tertiary);
  margin-top: 2px;
}

.trace-input code,
.trace-output code {
  color: var(--pv-text-secondary);
  word-break: break-all;
}

.trace-error {
  color: var(--pv-danger);
  font-weight: 600;
  font-size: 11px;
  margin-top: 2px;
}

.typing {
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px;
  border-top: 1px solid var(--pv-border);
}

.quick-tag {
  cursor: pointer;
  background: rgba(0, 240, 255, 0.1);
  border-color: rgba(0, 240, 255, 0.2);
}

.chat-input-area {
  display: flex;
  gap: 10px;
  padding: 12px;
  border-top: 1px solid var(--pv-border);
}

.chat-input-area :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.04);
  border-color: var(--pv-border);
  color: var(--pv-text-primary);
}
</style>
