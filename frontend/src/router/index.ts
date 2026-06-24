import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true },
    },
    {
      path: '/stations',
      name: 'stations',
      component: () => import('@/views/StationListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/stations/:id',
      name: 'station-detail',
      component: () => import('@/views/StationDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/stations/:id/diagnosis',
      name: 'diagnosis-report',
      component: () => import('@/views/DiagnosisReportView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/alarms',
      name: 'alarms',
      component: () => import('@/views/AlarmCenterView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/workorders',
      name: 'workorders',
      component: () => import('@/views/WorkOrderView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/reports',
      name: 'reports',
      component: () => import('@/views/ReportCenterView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/devices',
      name: 'devices',
      component: () => import('@/views/DeviceAnalysisView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/devices/manage',
      name: 'device-management',
      component: () => import('@/views/DeviceManagementView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  if (to.meta.public) {
    next()
    return
  }

  if (!authStore.isAuthenticated) {
    next('/login')
    return
  }

  // 尝试获取用户信息（如果还没有）
  if (!authStore.user) {
    try {
      await authStore.fetchUser()
    } catch {
      next('/login')
      return
    }
  }

  next()
})

export default router
