<template>
  <div class="pv-loading" :class="{ fullscreen }">
    <div class="pv-loading-spinner">
      <div class="pv-loading-ring" />
      <div v-if="text" class="pv-loading-text">{{ text }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  text?: string
  fullscreen?: boolean
}>()
</script>

<style scoped>
.pv-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.pv-loading.fullscreen {
  position: fixed;
  inset: 0;
  background: rgba(5, 9, 20, 0.8);
  backdrop-filter: blur(4px);
  z-index: 2000;
}

.pv-loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.pv-loading-ring {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 3px solid transparent;
  border-top-color: var(--pv-primary);
  border-right-color: var(--pv-primary-light);
  animation: pv-spin 1s linear infinite;
  box-shadow: 0 0 16px rgba(0, 240, 255, 0.3);
}

@keyframes pv-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.pv-loading-text {
  font-size: 13px;
  color: var(--pv-text-secondary);
  letter-spacing: 1px;
}
</style>
