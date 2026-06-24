import { ref, computed, onMounted, onUnmounted } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'pvops-theme'

const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

function getStoredTheme(): ThemeMode {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (raw === 'light' || raw === 'dark' || raw === 'system') return raw
  return 'system'
}

function resolveSystemTheme(): 'light' | 'dark' {
  return mediaQuery.matches ? 'dark' : 'light'
}

function applyTheme(mode: ThemeMode) {
  const resolved = mode === 'system' ? resolveSystemTheme() : mode
  const root = document.documentElement
  root.classList.remove('light', 'dark')
  root.classList.add(resolved)
  root.style.colorScheme = resolved
}

const theme = ref<ThemeMode>(getStoredTheme())

export function useTheme() {
  const resolvedTheme = computed<'light' | 'dark'>(() =>
    theme.value === 'system' ? resolveSystemTheme() : theme.value
  )

  const setTheme = (mode: ThemeMode) => {
    theme.value = mode
    localStorage.setItem(STORAGE_KEY, mode)
    applyTheme(mode)
  }

  const toggleTheme = () => {
    const order: ThemeMode[] = ['light', 'dark', 'system']
    const next = order[(order.indexOf(theme.value) + 1) % order.length]
    setTheme(next)
  }

  const systemListener = (_e: MediaQueryListEvent) => {
    if (theme.value === 'system') {
      applyTheme('system')
    }
  }

  onMounted(() => {
    applyTheme(theme.value)
    mediaQuery.addEventListener('change', systemListener)
  })

  onUnmounted(() => {
    mediaQuery.removeEventListener('change', systemListener)
  })

  return {
    theme,
    resolvedTheme,
    setTheme,
    toggleTheme,
  }
}

export function initTheme() {
  applyTheme(getStoredTheme())
}
