<template>
  <el-dropdown trigger="click" @command="handleCommand">
    <el-button text class="theme-switcher-btn" :title="currentLabel">
      <el-icon size="18">
        <Sunny v-if="resolvedTheme === 'light'" />
        <Moon v-else-if="resolvedTheme === 'dark'" />
        <Monitor v-else />
      </el-icon>
      <span class="theme-label">{{ currentLabel }}</span>
      <el-icon class="arrow"><ArrowDown /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="light" :class="{ active: theme === 'light' }">
          <el-icon><Sunny /></el-icon> 浅色
        </el-dropdown-item>
        <el-dropdown-item command="dark" :class="{ active: theme === 'dark' }">
          <el-icon><Moon /></el-icon> 深色
        </el-dropdown-item>
        <el-dropdown-item command="system" :class="{ active: theme === 'system' }">
          <el-icon><Monitor /></el-icon> 跟随系统
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Sunny, Moon, Monitor, ArrowDown } from '@element-plus/icons-vue'
import { useTheme, type ThemeMode } from '@/composables/useTheme'

const { theme, resolvedTheme, setTheme } = useTheme()

const labels: Record<ThemeMode, string> = {
  light: '浅色',
  dark: '深色',
  system: '跟随系统',
}

const currentLabel = computed(() => labels[theme.value])

const handleCommand = (cmd: ThemeMode) => {
  setTheme(cmd)
}
</script>

<style scoped>
.theme-switcher-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--pv-text-secondary);
  padding: 6px 10px;
  border-radius: 10px;
}
.theme-switcher-btn:hover {
  color: var(--pv-primary);
  background: var(--el-fill-color-light);
}
.theme-label {
  font-size: 13px;
  font-weight: 500;
}
.arrow {
  font-size: 12px;
  opacity: 0.6;
}
</style>

<style>
.el-dropdown-menu__item.active {
  color: var(--pv-primary);
  background: var(--el-fill-color-light);
}
</style>
