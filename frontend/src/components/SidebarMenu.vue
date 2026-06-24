<template>
  <el-menu
    :default-active="$route.path"
    router
    class="menu"
    background-color="transparent"
    text-color="#94a3b8"
    active-text-color="#00f0ff"
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
      <span>工单管理</span>
    </el-menu-item>
    <el-menu-item index="/reports">
      <el-icon><Document /></el-icon>
      <span>报告中心</span>
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
import { Odometer, OfficeBuilding, Warning, Tickets, Document, SetUp } from '@element-plus/icons-vue'
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
  color: #94a3b8;
  transition: all 0.25s ease;
}

.menu :deep(.el-menu-item:hover) {
  background: rgba(0, 240, 255, 0.06);
  color: #e0faff;
}

.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(0, 240, 255, 0.18), rgba(0, 240, 255, 0.03));
  color: #00f0ff;
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
  color: #94a3b8;
  transition: all 0.25s ease;
}

.menu :deep(.el-sub-menu__title:hover) {
  background: rgba(0, 240, 255, 0.06);
  color: #e0faff;
}

.menu :deep(.el-sub-menu.is-active .el-sub-menu__title) {
  color: #00f0ff;
  text-shadow: 0 0 12px rgba(0, 240, 255, 0.4);
}

.menu :deep(.el-sub-menu .el-menu-item) {
  height: 46px;
  margin-bottom: 6px;
  padding-left: 52px !important;
}

.menu :deep(.el-sub-menu .el-menu-item.is-active) {
  box-shadow: inset 3px 0 0 #00f0ff, 0 0 16px rgba(0, 240, 255, 0.12);
}
</style>
