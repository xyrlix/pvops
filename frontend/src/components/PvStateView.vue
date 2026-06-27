<template>
  <div class="pv-state" :style="containerStyle">
    <!-- loading: 骨架屏 -->
    <template v-if="state === 'loading'">
      <slot name="loading">
        <PvSkeleton :variant="variant" :rows="rows" />
      </slot>
    </template>

    <!-- empty: 空态 -->
    <template v-else-if="state === 'empty'">
      <slot name="empty">
        <PvEmpty :description="emptyText" />
      </slot>
    </template>

    <!-- error: 错误态（可点击重试） -->
    <template v-else-if="state === 'error'">
      <div class="pv-state__error">
        <el-icon :size="32" color="#F87171"><WarningFilled /></el-icon>
        <div class="pv-state__msg">{{ errorText || '加载失败' }}</div>
        <el-button v-if="onRetry" type="primary" plain size="small" @click="onRetry">
          <el-icon><Refresh /></el-icon>重试
        </el-button>
      </div>
    </template>

    <!-- normal: 正常渲染 children -->
    <template v-else>
      <slot />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { WarningFilled, Refresh } from '@element-plus/icons-vue'
import PvSkeleton from './PvSkeleton.vue'
import PvEmpty from './PvEmpty.vue'

export type PvState = 'loading' | 'empty' | 'error' | 'normal'

const props = withDefaults(defineProps<{
  state: PvState
  /** 加载中骨架变体（table / chart / text / paragraph / card） */
  variant?: 'text' | 'paragraph' | 'card' | 'chart' | 'table'
  /** 骨架行数 */
  rows?: number
  /** 空态文案 */
  emptyText?: string
  /** 错误态文案 */
  errorText?: string
  /** 错误态点击重试 */
  onRetry?: () => void
  /** 容器最小高度（避免空态塌缩） */
  minHeight?: number | string
}>(), {
  variant: 'text',
  rows: 3,
  emptyText: '暂无数据',
  errorText: '',
  onRetry: undefined,
  minHeight: undefined,
})

const containerStyle = computed(() => ({
  minHeight: typeof props.minHeight === 'number' ? `${props.minHeight}px` : props.minHeight || undefined,
}))
</script>

<style scoped>
.pv-state {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pv-state__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 16px;
  color: var(--pv-text-secondary);
}

.pv-state__msg {
  font-size: 13px;
  color: var(--pv-text-secondary);
  text-align: center;
  max-width: 320px;
}
</style>