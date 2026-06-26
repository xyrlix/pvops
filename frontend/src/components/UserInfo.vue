<template>
  <div class="user-info">
    <el-dropdown trigger="click" @command="handleCommand">
      <div class="user-trigger">
        <div class="avatar">
          {{ initials }}
        </div>
        <div class="user-meta">
          <div class="user-name">{{ displayName }}</div>
          <div class="user-role">{{ roleText }}</div>
        </div>
        <el-icon class="arrow"><ArrowDown /></el-icon>
      </div>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="profile">个人信息</el-dropdown-item>
          <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const displayName = computed(() => authStore.user?.full_name || authStore.user?.username || '用户')

const initials = computed(() => {
  const name = authStore.user?.full_name || authStore.user?.username || 'U'
  return name.charAt(0).toUpperCase()
})

const roleText = computed(() => {
  const role = authStore.user?.role || 'operator'
  const map: Record<string, string> = {
    admin: '系统管理员',
    manager: '站长',
    operator: '运维工程师',
    viewer: '观察员',
  }
  return map[role] || role
})

const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.user-info {
  display: flex;
  align-items: center;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 10px 6px 6px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.user-trigger:hover {
  background: var(--el-fill-color-light);
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 15px;
  color: #fff;
  background: linear-gradient(135deg, var(--pv-primary), #0066ff);
  box-shadow: 0 0 16px var(--pv-glow-primary);
}

.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--pv-text-primary);
}

.user-role {
  font-size: 12px;
  color: var(--pv-text-tertiary);
}

.arrow {
  color: var(--pv-text-tertiary);
  font-size: 12px;
}
</style>
