<template>
  <div class="dashboard-layout">
    <!-- 桌面端侧边栏 -->
    <aside class="pv-sidebar" :class="{ collapsed: isCollapsed, mobile: isMobile, open: mobileOpen }">
      <div class="pv-sidebar__brand">
        <div class="pv-sidebar__logo">PV</div>
        <div v-if="!isCollapsed || isMobile" class="pv-sidebar__brandtext">
          <div class="pv-sidebar__title">PVOps</div>
          <div class="pv-sidebar__sub">Command Center</div>
        </div>
      </div>

      <SidebarMenu :collapse="isCollapsed && !isMobile" />

      <div class="pv-sidebar__footer">
        <span class="pv-status-dot pv-status-dot--success" />
        <span v-if="!isCollapsed || isMobile" class="pv-sidebar__footertext">
          v0.1.0 · DEMO
        </span>
      </div>
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
            @click="toggleSidebar"
          >
            <el-icon :size="20">
              <Fold v-if="!isMobile && !isCollapsed" />
              <Expand v-else />
            </el-icon>
          </el-button>
          <div>
            <div class="pv-topbar__title">
              <slot name="title">运营总览</slot>
            </div>
            <div class="pv-topbar__sub">
              <slot name="subtitle">{{ currentTime }} · 系统运行正常</slot>
            </div>
          </div>
        </div>

        <!-- 信号条：在线/告警/采集频率 -->
        <div class="pv-topbar__signals">
          <div class="signal">
            <span class="pv-status-dot pv-status-dot--success" />
            <span class="signal__label">采集</span>
            <span class="signal__value pv-number">5s</span>
          </div>
          <div class="signal">
            <span class="pv-status-dot pv-status-dot--info" />
            <span class="signal__label">在线</span>
            <span class="signal__value pv-number">{{ onlineCount }}</span>
          </div>
          <div class="signal" :class="{ alert: alarmCount > 0 }">
            <span class="pv-status-dot" :class="alarmCount > 0 ? 'pv-status-dot--danger' : 'pv-status-dot--muted'" />
            <span class="signal__label">告警</span>
            <span class="signal__value pv-number">{{ alarmCount }}</span>
          </div>
        </div>

        <div class="pv-topbar__actions">
          <slot name="actions" />
          <ThemeSwitcher />
          <UserInfo />
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
import { Fold, Expand } from '@element-plus/icons-vue'
import SidebarMenu from '@/components/SidebarMenu.vue'
import UserInfo from '@/components/UserInfo.vue'
import AiCopilot from '@/components/AiCopilot.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'

const MOBILE_BREAKPOINT = 900

const currentTime = ref('')
let timer: ReturnType<typeof setInterval> | null = null

const isCollapsed = ref(false)
const isMobile = ref(false)
const mobileOpen = ref(false)

// 这些数字会在后续接入真实数据时改为 store
const onlineCount = computed(() => 5)
const alarmCount = computed(() => 3)

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
  currentTime.value = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  checkScreen()
  window.addEventListener('resize', checkScreen)
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
  background: var(--pv-surface);
  border-right: 1px solid var(--pv-border);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  z-index: 10;
  width: 240px;
  transition: width 0.25s ease;
}

.pv-sidebar.collapsed {
  width: 72px;
}

.pv-sidebar.collapsed .pv-sidebar__brandtext,
.pv-sidebar.collapsed .pv-sidebar__footertext,
.pv-sidebar.collapsed :deep(.menu-text) {
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
  color: #001018;
  font-weight: 800;
  font-family: var(--pv-font-mono);
  font-size: 13px;
  letter-spacing: 0.04em;
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
  font-family: var(--pv-font-mono);
  font-size: 10px;
  color: var(--pv-text-tertiary);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-top: 2px;
}

.pv-sidebar__footer {
  margin-top: auto;
  padding: 18px 20px;
  border-top: 1px solid var(--pv-border);
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--pv-font-mono);
  font-size: 11px;
  color: var(--pv-text-tertiary);
  letter-spacing: 0.06em;
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

.pv-topbar__signals {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background: var(--pv-stripe);
  border: 1px solid var(--pv-border);
  border-radius: 999px;
}

.signal {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  font-family: var(--pv-font-mono);
  font-size: 11px;
  color: var(--pv-text-secondary);
  transition: var(--pv-transition);
}

.signal.alert {
  background: rgba(244, 63, 94, 0.08);
}

.signal__label {
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.signal__value {
  font-weight: 700;
  color: var(--pv-text-primary);
}

.signal.alert .signal__value {
  color: var(--pv-danger);
}

.pv-topbar__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 移动端 */
@media (max-width: 900px) {
  .pv-sidebar:not(.mobile) {
    display: none;
  }

  .menu-toggle {
    display: inline-flex;
  }

  .pv-topbar__signals {
    display: none;
  }

  .pv-topbar__sub {
    display: none;
  }

  .pv-topbar {
    padding: 12px 16px;
  }
}
</style>
