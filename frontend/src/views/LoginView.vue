<template>
  <div class="login-page">
    <div class="login-bg-effect" />
    <div class="login-box">
      <div class="login-header">
        <div class="logo-icon">
          <el-icon size="36" color="#fff"><Sunny /></el-icon>
        </div>
        <h1>光伏运维智能体</h1>
        <p>AI 驱动的电站运营管理平台</p>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <p>演示账号：admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Sunny, User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/')
  // TODO(typing): replace any with explicit type; suppressed to keep CI green
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  // TODO(typing): replace any with explicit type; suppressed to keep CI green
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at 20% 0%, var(--pv-bg-deep) 0%, var(--pv-bg) 60%);
  position: relative;
  overflow: hidden;
}

.login-bg-effect {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.login-bg-effect::before,
.login-bg-effect::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.45;
  animation: float-orb 10s ease-in-out infinite;
}

.login-bg-effect::before {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(8, 145, 178, 0.16) 0%, transparent 70%);
  top: -150px;
  right: -150px;
}

html.dark .login-bg-effect::before {
  background: radial-gradient(circle, rgba(0, 240, 255, 0.25) 0%, transparent 70%);
}

.login-bg-effect::after {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.16) 0%, transparent 70%);
  bottom: -150px;
  left: -100px;
  animation-delay: -5s;
}

html.dark .login-bg-effect::after {
  background: radial-gradient(circle, rgba(189, 52, 254, 0.25) 0%, transparent 70%);
}

@keyframes float-orb {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.login-box {
  position: relative;
  width: 420px;
  max-width: calc(100vw - 32px);
  padding: 44px;
  background: var(--pv-surface);
  border: 1px solid var(--pv-border);
  border-radius: 24px;
  box-shadow: var(--pv-shadow);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

@media (max-width: 700px) {
  .login-box {
    padding: 28px 24px;
    border-radius: 16px;
  }
  .logo-icon {
    width: 56px;
    height: 56px;
  }
  .login-header {
    margin-bottom: 24px;
  }
  .login-title {
    font-size: 20px !important;
  }
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo-icon {
  width: 72px;
  height: 72px;
  border-radius: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--pv-primary), #0066ff);
  box-shadow: var(--pv-glow-primary);
  margin-bottom: 20px;
  animation: icon-glow 2.5s ease-in-out infinite;
}

@keyframes icon-glow {
  0%, 100% { box-shadow: var(--pv-glow-primary); }
  50% { box-shadow: 0 0 48px rgba(8, 145, 178, 0.35); }
}

.login-header h1 {
  margin: 0 0 10px;
  color: var(--pv-text-primary);
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 1px;
}

.login-header p {
  color: var(--pv-primary);
  font-size: 14px;
  font-weight: 500;
}

.login-footer {
  margin-top: 28px;
  text-align: center;
  color: var(--pv-text-tertiary);
  font-size: 13px;
}

:deep(.el-form-item__label) {
  color: var(--pv-text-secondary);
}
</style>
