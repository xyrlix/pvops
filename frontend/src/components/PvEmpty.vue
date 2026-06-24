<template>
  <div class="pv-empty">
    <div class="pv-empty-icon">
      <el-icon :size="48" color="var(--pv-text-tertiary)"><component :is="icon" /></el-icon>
    </div>
    <div class="pv-empty-description">{{ description }}</div>
    <div v-if="$slots.default" class="pv-empty-extra">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  description?: string
  icon?: string
}>(), {
  description: '暂无数据',
  icon: 'DataLine',
})
</script>

<style scoped>
.pv-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.pv-empty-icon {
  margin-bottom: 14px;
  opacity: 0.6;
}

.pv-empty-description {
  font-size: 14px;
  color: var(--pv-text-tertiary);
  line-height: 1.6;
}

.pv-empty-extra {
  margin-top: 16px;
}
</style>
