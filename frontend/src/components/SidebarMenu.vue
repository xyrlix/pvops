<template>
  <div class="sidebar-menu">
    <!-- 导航项 -->
    <div class="nav-group">
      <div v-if="!collapse" class="nav-group__title">导航</div>
      <router-link v-for="item in mainNav" :key="item.path" :to="item.path" class="nav-item" :class="{ active: isActive(item) }">
        <el-icon :size="20"><component :is="item.icon" /></el-icon>
        <span v-if="!collapse" class="nav-label">{{ item.label }}</span>
        <span v-if="item.badge && !collapse" class="nav-badge" :class="`badge-${item.badgeLevel || 'info'}`">{{ item.badge }}</span>
      </router-link>
    </div>

    <div v-if="!collapse" class="nav-divider" />

    <div class="nav-group">
      <div v-if="!collapse" class="nav-group__title">管理</div>
      <router-link v-for="item in mgmtNav" :key="item.path" :to="item.path" class="nav-item" :class="{ active: isActive(item) }">
        <el-icon :size="20"><component :is="item.icon" /></el-icon>
        <span v-if="!collapse" class="nav-label">{{ item.label }}</span>
      </router-link>
    </div>

    <div class="nav-spacer" />

    <!-- 底部用户 -->
    <router-link to="/profile" class="nav-item nav-user" :class="{ active: isActive({ path: '/profile' }) }">
      <div class="nav-avatar">{{ userInitial }}</div>
      <div v-if="!collapse" class="nav-user-info">
        <div class="nav-user-name">{{ userName }}</div>
        <div class="nav-user-role">{{ roleLabel }}</div>
        <div class="nav-user-version">v0.1.0</div>
      </div>
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Odometer, ChatDotRound, Warning, Tickets, OfficeBuilding, Document, Collection, SetUp } from '@element-plus/icons-vue'

withDefaults(defineProps<{ collapse?: boolean }>(), { collapse: false })

const route = useRoute()
const authStore = useAuthStore()

const roleMap: Record<string, string> = { admin: '管理员', manager: '经理', operator: '运维', viewer: '只读', superadmin: '超级管理员' }
const userInitial = computed(() => (authStore.user?.full_name || authStore.user?.username || '管')[0])
const userName = computed(() => authStore.user?.full_name || authStore.user?.username || '管理员')
const roleLabel = computed(() => roleMap[authStore.user?.role || ''] || '管理员')

const mainNav = [
  { path: '/', label: '总览大屏', icon: Odometer, badge: undefined },
  { path: '/agent', label: 'AI 智能体', icon: ChatDotRound, badge: 'NEW', badgeLevel: 'info' },
  { path: '/alarms', label: '告警中心', icon: Warning, badge: undefined },
  { path: '/workorders', label: '运维工单', icon: Tickets, badge: undefined },
]

const mgmtNav = [
  { path: '/stations', label: '电站管理', icon: OfficeBuilding },
  { path: '/devices/manage', label: '设备管理', icon: SetUp },
  { path: '/reports', label: '运维简报', icon: Document },
  { path: '/knowledge', label: '知识库', icon: Collection },
]

const isActive = (item: { path: string }) => {
  if (item.path === '/') return route.path === '/'
  return route.path.startsWith(item.path)
}
</script>

<style scoped>
.sidebar-menu {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  padding: 4px 12px 8px;
  gap: 2px;
}

.nav-group__title {
  font-size: 10px;
  font-weight: 700;
  color: var(--pv-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  padding: 12px 12px 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--pv-text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.18s ease;
  cursor: pointer;
  position: relative;
}

.nav-item:hover {
  background: var(--pv-stripe);
  color: var(--pv-text-primary);
}

.nav-item.active {
  background: linear-gradient(90deg, rgba(96, 165, 250, 0.12), transparent);
  color: var(--pv-primary);
  font-weight: 600;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 3px;
  border-radius: 2px;
  background: var(--pv-primary);
  box-shadow: var(--pv-glow-primary);
}

.nav-label {
  flex: 1;
  min-width: 0;
}

.nav-badge {
  font-size: 9px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 6px;
  letter-spacing: 0.04em;
  font-family: var(--pv-font-mono);
}

.badge-info {
  background: rgba(56, 189, 248, 0.15);
  color: var(--pv-info);
}

.badge-warning {
  background: rgba(251, 191, 36, 0.15);
  color: var(--pv-warning);
}

.nav-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--pv-border), transparent);
  margin: 6px 12px;
}

.nav-spacer {
  flex: 1;
}

.nav-user {
  margin-top: 4px;
  border-top: 1px solid var(--pv-border);
  padding-top: 12px;
}

.nav-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--pv-primary), var(--pv-accent));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0B1120;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.nav-user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.nav-user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--pv-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-user-role {
  font-size: 10px;
  color: var(--pv-text-tertiary);
  font-family: var(--pv-font-mono);
  letter-spacing: 0.06em;
}

.nav-user-version {
  font-size: 9px;
  color: var(--pv-text-tertiary);
  opacity: 0.4;
  font-family: var(--pv-font-mono);
  letter-spacing: 0.04em;
  margin-top: 1px;
}
</style>