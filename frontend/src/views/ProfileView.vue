<template>
  <DashboardLayout>
    <template #title>
      <span class="pv-page-title">个人中心</span>
    </template>
    <template #subtitle>PROFILE · 账号信息与偏好</template>

    <el-row :gutter="20">
      <el-col :xs="24" :md="8">
        <PvCard title="账号信息" icon="User" glow>
          <div v-if="user" class="profile-section">
            <div class="profile-avatar">{{ (user.full_name || user.username || '?')[0] }}</div>
            <div class="profile-name">{{ user.full_name || user.username }}</div>
            <div class="profile-role">{{ levelLabel(user.role) }}</div>
            <el-divider />
            <div class="profile-detail">
              <span>用户名</span><span>{{ user.username }}</span>
            </div>
            <div class="profile-detail">
              <span>邮箱</span><span>{{ user.email || '-' }}</span>
            </div>
            <div class="profile-detail">
              <span>角色</span><span>{{ user.role }}</span>
            </div>
          </div>
        </PvCard>
      </el-col>

      <el-col :xs="24" :md="8">
        <PvCard title="主题偏好" icon="Brush" glow>
          <div class="profile-section">
            <div class="theme-options">
              <div
                v-for="opt in themeOptions"
                :key="opt.value"
                class="theme-option"
                :class="{ active: theme === opt.value }"
                @click="setTheme(opt.value)"
              >
                <el-icon :size="20">{{ opt.icon }}</el-icon>
                <span>{{ opt.label }}</span>
              </div>
            </div>
          </div>
        </PvCard>
      </el-col>

      <el-col :xs="24" :md="8">
        <PvCard title="安全" icon="Lock" glow>
          <div class="profile-section">
            <p style="font-size:13px;color:var(--pv-text-secondary);margin:0 0 12px">当前通过 JWT 令牌认证</p>
            <el-button type="danger" plain @click="handleLogout">
              <el-icon><SwitchButton /></el-icon> 退出登录
            </el-button>
          </div>
        </PvCard>
      </el-col>
    </el-row>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Sunny, Moon, Monitor, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useTheme, type ThemeMode } from '@/composables/useTheme'
import DashboardLayout from '@/components/DashboardLayout.vue'
import PvCard from '@/components/PvCard.vue'

const router = useRouter()
const authStore = useAuthStore()
const { theme, setTheme } = useTheme()

const user = computed(() => authStore.user)

const themeOptions = [
  { value: 'light' as ThemeMode, label: '浅色', icon: Sunny },
  { value: 'dark' as ThemeMode, label: '深色', icon: Moon },
  { value: 'system' as ThemeMode, label: '跟随系统', icon: Monitor },
]

const levelLabel = (role: string) => {
  const map: Record<string, string> = { admin: '管理员', manager: '经理', operator: '运维', viewer: '只读', superadmin: '超级管理员' }
  return map[role] || role
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('pvops-chat-history')
  router.push('/login')
}
</script>

<style scoped>
.profile-section { display: flex; flex-direction: column; align-items: center; }
.profile-avatar {
  width: 64px; height: 64px; border-radius: 50%;
  background: linear-gradient(135deg, var(--pv-primary), var(--pv-accent));
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 700; color: #fff;
  margin-bottom: 12px;
}
.profile-name { font-size: 18px; font-weight: 700; color: var(--pv-text-primary); }
.profile-role { font-size: 12px; color: var(--pv-text-tertiary); font-family: var(--pv-font-mono); margin-bottom: 8px; }
.profile-detail {
  display: flex; justify-content: space-between; width: 100%;
  padding: 8px 0; font-size: 13px;
  border-bottom: 1px solid var(--pv-border);
}
.profile-detail span:first-child { color: var(--pv-text-tertiary); }
.profile-detail span:last-child { color: var(--pv-text-primary); font-weight: 500; }
.theme-options { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
.theme-option {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 14px 20px; border-radius: 12px;
  border: 2px solid var(--pv-border); cursor: pointer;
  transition: var(--pv-transition); background: var(--pv-surface);
}
.theme-option:hover { border-color: var(--pv-primary); }
.theme-option.active { border-color: var(--pv-primary); background: rgba(96, 165, 250, 0.1); }
</style>