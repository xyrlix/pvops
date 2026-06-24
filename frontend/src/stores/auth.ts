import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/services/api'

export interface User {
  id: number
  username: string
  email?: string
  full_name?: string
  role: string
  status: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)
  const isAuthenticated = ref(!!token.value)

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
    isAuthenticated.value = true
  }

  const clearAuth = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    isAuthenticated.value = false
  }

  const login = async (username: string, password: string) => {
    const data = (await authApi.login({ username, password })) as unknown as {
      access_token: string
      user: User
    }
    setToken(data.access_token)
    user.value = data.user
    return data
  }

  const logout = () => {
    clearAuth()
  }

  const fetchUser = async () => {
    if (!token.value) return
    try {
      const data = (await authApi.me()) as unknown as User
      user.value = data
      isAuthenticated.value = true
    } catch (err) {
      clearAuth()
      throw err
    }
  }

  const hasRole = (roles: string[]) => {
    return user.value ? roles.includes(user.value.role) : false
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
    fetchUser,
    setToken,
    clearAuth,
    hasRole,
  }
})
