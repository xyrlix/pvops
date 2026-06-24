<template>
  <div class="dashboard-layout">
    <div class="tech-bg">
      <div class="grid-overlay" />
      <div class="orb orb-1" />
      <div class="orb orb-2" />
      <div class="orb orb-3" />
      <div class="scanline" />
    </div>

    <!-- 桌面端侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: isCollapsed, mobile: isMobile, open: mobileOpen }">
      <div class="logo">
        <div class="logo-icon">
          <el-icon size="32" color="#fff"><Sunny /></el-icon>
        </div>
        <div class="logo-text">
          <div class="logo-title">光伏运维智能体</div>
          <div class="logo-subtitle">PVOps</div>
        </div>
      </div>
      <SidebarMenu :collapse="isCollapsed && !isMobile" />
      <div class="sidebar-footer">
        <div class="version">v0.1.0</div>
        <div class="env-tag">DEMO</div>
      </div>
    </aside>

    <!-- 移动端遮罩 -->
    <div
      v-if="isMobile && mobileOpen"
      class="sidebar-overlay"
      @click="mobileOpen = false"
    />

    <div class="main-area">
      <header class="top-header">
        <div class="header-left">
          <el-button text class="menu-toggle" @click="toggleSidebar">
            <el-icon :size="22"><Fold v-if="!isMobile && !isCollapsed" /><Expand v-else /></el-icon>
          </el-button>
          <div class="breadcrumb">
            <slot name="breadcrumb" />
          </div>
          <div class="header-status">
            <span class="status-dot" />
            <span class="status-text">系统运行正常</span>
            <span class="header-time">{{ currentTime }}</span>
          </div>
        </div>
        <div class="header-actions">
          <slot name="actions" />
          <ThemeSwitcher />
          <UserInfo />
        </div>
      </header>
      <main class="main-content">
        <slot />
      </main>
      <AiCopilot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { Sunny, Fold, Expand } from '@element-plus/icons-vue'
import SidebarMenu from '@/components/SidebarMenu.vue'
import UserInfo from '@/components/UserInfo.vue'
import AiCopilot from '@/components/AiCopilot.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'

const MOBILE_BREAKPOINT = 768

const currentTime = ref('')
let timer: ReturnType<typeof setInterval> | null = null

const isCollapsed = ref(false)
const isMobile = ref(false)
const mobileOpen = ref(false)

const checkScreen = () => {
  isMobile.value = window.innerWidth <= MOBILE_BREAKPOINT
  if (!isMobile.value) {
    mobileOpen.value = false
  }
}

const toggleSidebar = () => {
  if (isMobile.value) {
    mobileOpen.value = !mobileOpen.value
  } else {
    isCollapsed.value = !isCollapsed.value
  }
}

const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
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
  background: var(--pv-bg);
  position: relative;
  overflow: hidden;
}

.tech-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(8, 145, 178, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(8, 145, 178, 0.04) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
}

html.dark .grid-overlay {
  background-image:
    linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: float 10s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: #00f0ff;
  top: -150px;
  right: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: #bd34fe;
  bottom: -120px;
  left: 10%;
  animation-delay: -3s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: #00ff9d;
  top: 40%;
  right: 20%;
  animation-delay: -6s;
  opacity: 0.2;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.scanline {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 240, 255, 0.015) 2px,
    rgba(0, 240, 255, 0.015) 4px
  );
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--pv-surface);
  border-right: 1px solid var(--pv-border);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  position: relative;
  z-index: 10;
  transition: width 0.25s ease;
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar.collapsed .logo-text,
.sidebar.collapsed .sidebar-footer {
  display: none;
}

.sidebar.collapsed .logo {
  justify-content: center;
  padding: 26px 12px;
}

.sidebar.mobile {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 260px;
  transform: translateX(-100%);
  transition: transform 0.25s ease;
  z-index: 200;
}

.sidebar.mobile.open {
  transform: translateX(0);
}

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(2px);
  z-index: 150;
}

.logo {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 26px 24px;
  border-bottom: 1px solid var(--pv-border);
  flex-shrink: 0;
}

.logo-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: linear-gradient(135deg, #00f0ff, #0066ff);
  box-shadow: 0 0 24px rgba(0, 240, 255, 0.45);
  animation: icon-glow 2.5s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes icon-glow {
  0%, 100% { box-shadow: 0 0 24px rgba(0, 240, 255, 0.45); }
  50% { box-shadow: 0 0 40px rgba(0, 240, 255, 0.7); }
}

.logo-title {
  font-size: 18px;
  font-weight: 800;
  color: var(--pv-text-primary);
  letter-spacing: 0.5px;
  text-shadow: 0 0 16px rgba(0, 240, 255, 0.4);
  white-space: nowrap;
}

.logo-subtitle {
  font-size: 12px;
  font-weight: 700;
  color: var(--pv-primary);
  letter-spacing: 2px;
}

.sidebar-footer {
  margin-top: auto;
  padding: 20px 24px;
  border-top: 1px solid var(--pv-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--pv-text-tertiary);
  font-size: 12px;
  flex-shrink: 0;
}

.env-tag {
  padding: 3px 10px;
  border-radius: 6px;
  background: rgba(0, 240, 255, 0.12);
  color: var(--pv-primary);
  font-weight: 700;
  font-size: 11px;
  box-shadow: 0 0 12px rgba(0, 240, 255, 0.2);
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  position: relative;
  z-index: 10;
}

.top-header {
  height: 72px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  background: var(--pv-surface);
  border-bottom: 1px solid var(--pv-border);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.menu-toggle {
  display: none;
  align-self: flex-start;
  color: var(--pv-text-secondary);
  padding: 6px;
  border-radius: 8px;
}

.menu-toggle:hover {
  color: var(--pv-primary);
  background: var(--el-fill-color-light);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 19px;
  font-weight: 800;
  color: var(--pv-text-primary);
}

.breadcrumb :deep(.back-icon) {
  cursor: pointer;
  color: var(--pv-primary);
  transition: transform 0.2s, filter 0.2s;
}

.breadcrumb :deep(.back-icon:hover) {
  transform: scale(1.1);
  filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.6));
}

.header-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--pv-text-tertiary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--pv-success);
  box-shadow: 0 0 10px var(--pv-success);
  animation: status-blink 2s infinite;
}

@keyframes status-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.header-time {
  margin-left: 12px;
  font-family: var(--pv-font-display);
  color: var(--pv-text-secondary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 18px;
}

.main-content {
  flex: 1;
  padding: 28px;
  overflow: auto;
}

@media (max-width: 768px) {
  .sidebar:not(.mobile) {
    display: none;
  }

  .menu-toggle {
    display: inline-flex;
  }

  .top-header {
    height: 64px;
    padding: 0 16px;
  }

  .header-left {
    gap: 4px;
  }

  .breadcrumb {
    font-size: 16px;
  }

  .header-status {
    display: none;
  }

  .header-actions {
    gap: 8px;
  }

  .main-content {
    padding: 16px;
  }
}
</style>
