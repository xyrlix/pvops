<template>
  <el-menu
    :default-active="$route.path"
    router
    class="menu"
    :collapse="collapse"
    collapse-transition
    background-color="transparent"
    :text-color="menuText"
    :active-text-color="menuActive"
  >
    <el-menu-item index="/">
      <el-icon><Odometer /></el-icon>
      <span>总览大屏</span>
    </el-menu-item>
    <el-menu-item index="/stations">
      <el-icon><OfficeBuilding /></el-icon>
      <span>电站管理</span>
    </el-menu-item>
    <el-menu-item index="/alarms">
      <el-icon><Warning /></el-icon>
      <span>告警中心</span>
    </el-menu-item>
    <el-menu-item index="/workorders">
      <el-icon><Tickets /></el-icon>
      <span>运维工单</span>
    </el-menu-item>
    <el-menu-item index="/reports">
      <el-icon><Document /></el-icon>
      <span>运维简报</span>
    </el-menu-item>
    <el-menu-item index="/knowledge">
      <el-icon><Collection /></el-icon>
      <span>知识库</span>
    </el-menu-item>
    <el-sub-menu index="/devices">
      <template #title>
        <el-icon><SetUp /></el-icon>
        <span>设备</span>
      </template>
      <el-menu-item index="/devices/manage">设备管理</el-menu-item>
      <el-menu-item index="/devices">设备分析</el-menu-item>
    </el-sub-menu>
  </el-menu>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Odometer, OfficeBuilding, Warning, Tickets, Document, SetUp, Collection } from '@element-plus/icons-vue'
import { useTheme } from '@/composables/useTheme'

withDefaults(defineProps<{ collapse?: boolean }>(), { collapse: false })

const { resolvedTheme } = useTheme()

const menuText = computed(() => (resolvedTheme.value === 'dark' ? '#94a3b8' : '#64748b'))
const menuActive = computed(() => (resolvedTheme.value === 'dark' ? '#00f0ff' : '#0891b2'))
</script>

<style scoped>
.menu {
  border-right: none;
  padding: 16px;
  background: transparent;
}

.menu :deep(.el-menu-item) {
  height: 54px;
  margin-bottom: 10px;
  border-radius: 14px;
  font-size: 14px;
  font-weight: 600;
  color: var(--pv-text-tertiary);
  transition: all 0.25s ease;
}

.menu :deep(.el-menu-item:hover) {
  background: rgba(8, 145, 178, 0.06);
  color: var(--pv-text-primary);
}

html.dark .menu :deep(.el-menu-item:hover) {
  background: rgba(0, 240, 255, 0.06);
  color: #e0faff;
}

.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(8, 145, 178, 0.14), rgba(8, 145, 178, 0.03));
  color: var(--pv-primary);
  box-shadow:
    inset 3px 0 0 var(--pv-primary),
    0 0 20px rgba(8, 145, 178, 0.1);
  text-shadow: 0 0 12px rgba(8, 145, 178, 0.3);
}

html.dark .menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(0, 240, 255, 0.18), rgba(0, 240, 255, 0.03));
  box-shadow:
    inset 3px 0 0 #00f0ff,
    0 0 20px rgba(0, 240, 255, 0.15);
  text-shadow: 0 0 12px rgba(0, 240, 255, 0.5);
}

.menu :deep(.el-menu-item .el-icon) {
  font-size: 19px;
  margin-right: 12px;
}

.menu :deep(.el-sub-menu__title) {
  height: 54px;
  border-radius: 14px;
  font-size: 14px;
  font-weight: 600;
  color: var(--pv-text-tertiary);
  transition: all 0.25s ease;
}

.menu :deep(.el-sub-menu__title:hover) {
  background: rgba(8, 145, 178, 0.06);
  color: var(--pv-text-primary);
}

html.dark .menu :deep(.el-sub-menu__title:hover) {
  background: rgba(0, 240, 255, 0.06);
  color: #e0faff;
}

.menu :deep(.el-sub-menu.is-active .el-sub-menu__title) {
  color: var(--pv-primary);
  text-shadow: 0 0 12px rgba(8, 145, 178, 0.25);
}

html.dark .menu :deep(.el-sub-menu.is-active .el-sub-menu__title) {
  text-shadow: 0 0 12px rgba(0, 240, 255, 0.4);
}

.menu :deep(.el-sub-menu .el-menu-item) {
  height: 46px;
  margin-bottom: 6px;
  padding-left: 52px !important;
}

.menu :deep(.el-sub-menu .el-menu-item.is-active) {
  box-shadow: inset 3px 0 0 var(--pv-primary), 0 0 16px rgba(8, 145, 178, 0.08);
}

html.dark .menu :deep(.el-sub-menu .el-menu-item.is-active) {
  box-shadow: inset 3px 0 0 #00f0ff, 0 0 16px rgba(0, 240, 255, 0.12);
}
</style>
