<template>
  <div class="dashboard-layout">
    <!-- 桌面端侧边栏 -->
    <aside class="pv-sidebar" :class="{ collapsed: isCollapsed, mobile: isMobile, open: mobileOpen }">
      <div class="pv-sidebar__brand">
        <div class="pv-sidebar__logo">☀</div>
        <div v-if="!isCollapsed || isMobile" class="pv-sidebar__brandtext">
          <div class="pv-sidebar__title">PVOps</div>
          <div class="pv-sidebar__sub">智能运维</div>
        </div>
      </div>

      <SidebarMenu :collapse="isCollapsed && !isMobile" />
    </aside>

    <!-- 移动端遮罩 -->
    <div
      v-if="isMobile && mobileOpen"
      class="sidebar-overlay"
      @click="mobileOpen = false"
    />

    <div class="main-area">
      <header class="pv-topbar">
        <div class="pv-topbar__brand">
          <el-button
            text
            class="menu-toggle"
            :title="isMobile ? '打开菜单' : (isCollapsed ? '展开侧栏' : '折叠侧栏')"
            :aria-label="isMobile ? '打开菜单' : (isCollapsed ? '展开侧栏' : '折叠侧栏')"
            @click="toggleSidebar"
          >
            <el-icon :size="20">
              <Fold v-if="!isMobile && !isCollapsed" />
              <Expand v-else />
            </el-icon>
          </el-button>
          <div>
            <div v-if="$slots.title" class="pv-topbar__title">
              <slot name="title" />
            </div>
            <div v-else class="pv-topbar__title">光伏电站智能运营系统</div>
            <div v-if="$slots.subtitle" class="pv-topbar__sub">
              <slot name="subtitle" />
            </div>
            <div v-else class="pv-topbar__sub">PV INTELLIGENT OPERATION SYSTEM</div>
          </div>
        </div>

        <div class="pv-topbar__right">
          <el-tooltip
            :content="deviceStatus.tooltip"
            placement="bottom"
            :show-after="200"
          >
            <div class="pv-topbar__status">
              <span :class="['pv-status-dot', `pv-status-dot--${deviceStatus.tone}`]" />
              <span class="pv-topbar__status-label">{{ deviceStatus.label }}</span>
            </div>
          </el-tooltip>
          <div class="pv-topbar__divider" />
          <div class="pv-topbar__time" :title="`服务器时间：${currentTime}`">{{ currentTime }}</div>
          <ThemeSwitcher />
          <el-tooltip content="个人中心" placement="bottom">
            <div class="pv-topbar__avatar" style="cursor:pointer" @click="goProfile">管</div>
          </el-tooltip>
        </div>
      </header>

      <main class="pv-page">
        <slot />
      </main>

      <AiCopilot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Fold, Expand } from '@element-plus/icons-vue'
import { useStationStore } from '@/stores/station'
import { dashboardApi } from '@/services/api'
import SidebarMenu from '@/components/SidebarMenu.vue'
import AiCopilot from '@/components/AiCopilot.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'

const MOBILE_BREAKPOINT = 900

const currentTime = ref('')
let timer: ReturnType<typeof setInterval> | null = null

const router = useRouter()
const isCollapsed = ref(false)
const isMobile = ref(false)
const mobileOpen = ref(false)

const stationStore = useStationStore()
const goProfile = () => router.push('/profile')

const checkScreen = () => {
  isMobile.value = window.innerWidth <= MOBILE_BREAKPOINT
  if (!isMobile.value) mobileOpen.value = false
}

const toggleSidebar = () => {
  if (isMobile.value) mobileOpen.value = !mobileOpen.value
  else isCollapsed.value = !isCollapsed.value
}

const updateTime = () => {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  currentTime.value = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// 顶栏设备状态：从 store 实时聚合
const deviceStatus = computed(() => {
  const stations = stationStore.stations || []
  const total = stations.length
  const online = stations.filter((s) => s.status === 'active').length
  const offline = total - online

  if (total === 0) {
    return {
      label: '等待数据接入',
      tooltip: '尚未配置电站 / 设备',
      tone: 'muted' as const,
    }
  }
  if (offline > 0) {
    return {
      label: `${online}/${total} 在线 · ${offline} 离线`,
      tooltip: `${offline} 个电站离线，请检查通信链路`,
      tone: 'warning' as const,
    }
  }
  return {
    label: `${online}/${total} 在线`,
    tooltip: '所有电站运行正常',
    tone: 'success' as const,
  }
})

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  checkScreen()
  window.addEventListener('resize', checkScreen)
  // 初次拉取总览，用于顶栏状态聚合
  if (stationStore.fetchStations) {
    stationStore.fetchStations()
  }
  // 静默拉总览（用于 KPI，但不阻塞渲染）
  dashboardApi.overview().catch(() => {})
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  window.removeEventListener('resize', checkScreen)
})
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  position: relative;
}

/* —— Sidebar —— */
.pv-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--pv-bg);
  border-right: 1px solid var(--pv-border);
  z-index: 5;
  width: 240px;
  transition: width 0.25s ease;
}

.pv-sidebar.collapsed {
  width: 72px;
}

.pv-sidebar.collapsed .pv-sidebar__brandtext,
.pv-sidebar.collapsed :deep(.menu-text),
.pv-sidebar.collapsed :deep(.nav-label),
.pv-sidebar.collapsed :deep(.nav-user-info) {
  display: none;
}

.pv-sidebar.mobile {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 240px;
  transform: translateX(-100%);
  transition: transform 0.25s ease;
  z-index: 200;
}

.pv-sidebar.mobile.open {
  transform: translateX(0);
}

.pv-sidebar__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 22px 20px;
  border-bottom: 1px solid var(--pv-border);
}

.pv-sidebar__logo {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--pv-primary), var(--pv-accent));
  display: grid;
  place-items: center;
  color: #0B1120;
  font-weight: 800;
  font-size: 18px;
  box-shadow: var(--pv-glow-primary);
  flex-shrink: 0;
}

.pv-sidebar__title {
  font-weight: 800;
  font-size: 16px;
  letter-spacing: 0.04em;
  color: var(--pv-text-primary);
}

.pv-sidebar__sub {
  font-size: 10px;
  color: var(--pv-text-tertiary);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-top: 2px;
}


.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
  z-index: 150;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* —— Topbar —— */
.pv-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  background: var(--pv-bg);
  border-bottom: 1px solid var(--pv-border);
  position: sticky;
  top: 0;
  z-index: 4;
}

.pv-topbar__brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.menu-toggle {
  color: var(--pv-text-secondary);
  padding: 6px;
  border-radius: 8px;
}
.menu-toggle:hover {
  color: var(--pv-primary);
  background: var(--el-fill-color-light);
}

.pv-topbar__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pv-topbar__title {
  font-size: 18px;
  color: var(--pv-text-primary);
  font-weight: 700;
}

.pv-topbar__sub {
  font-size: 11px;
  color: var(--pv-text-tertiary);
  letter-spacing: 2px;
  text-transform: uppercase;
}

.pv-topbar__right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.pv-topbar__status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pv-topbar__status-label {
  font-size: 12px;
  color: var(--pv-text-secondary);
}

.pv-topbar__divider {
  width: 1px;
  height: 20px;
  background: var(--pv-border);
}

.pv-topbar__time {
  font-size: 12px;
  color: var(--pv-text-secondary);
  font-family: var(--pv-font-mono);
}

.pv-topbar__avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 2px solid rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--pv-text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: var(--pv-transition);
}
.pv-topbar__avatar:hover {
  border-color: var(--pv-primary);
  color: var(--pv-primary);
}

/* 移动端 */
@media (max-width: 900px) {
  .pv-sidebar:not(.mobile) {
    display: none;
  }

  .menu-toggle {
    display: inline-flex;
  }

  .pv-topbar__sub,
  .pv-topbar__divider,
  .pv-topbar__status-label {
    display: none;
  }

  .pv-topbar {
    padding: 0 16px;
  }
}

@media (max-width: 700px) {
  .pv-topbar__time {
    display: none;
  }
}
</style>
