<template>
  <router-view v-slot="{ Component }">
    <transition name="page" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { initTheme } from '@/composables/useTheme'

const authStore = useAuthStore()

onMounted(() => {
  initTheme()
  // 如果有 token，尝试恢复用户信息
  if (authStore.token && !authStore.user) {
    authStore.fetchUser().catch(() => {
      // fetchUser 内部会清除无效 token
    })
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans SC', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: var(--pv-bg);
  color: var(--pv-text-primary);
  transition: background 0.3s ease, color 0.3s ease;
}
</style>
