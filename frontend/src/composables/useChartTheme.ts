import { computed } from 'vue'
import { useTheme } from './useTheme'

export interface ChartThemeColors {
  textPrimary: string
  textSecondary: string
  textTertiary: string
  grid: string
  splitLine: string
  tooltipBg: string
  tooltipBorder: string
  tooltipText: string
}

const dark: ChartThemeColors = {
  textPrimary: '#e0faff',
  textSecondary: '#94a3b8',
  textTertiary: '#64748b',
  grid: 'rgba(148, 163, 184, 0.08)',
  splitLine: 'rgba(148, 163, 184, 0.08)',
  tooltipBg: 'rgba(12, 18, 32, 0.92)',
  tooltipBorder: 'rgba(0, 240, 255, 0.2)',
  tooltipText: '#f0f9ff',
}

const light: ChartThemeColors = {
  textPrimary: '#0f172a',
  textSecondary: '#475569',
  textTertiary: '#94a3b8',
  grid: 'rgba(15, 23, 42, 0.06)',
  splitLine: 'rgba(15, 23, 42, 0.06)',
  tooltipBg: 'rgba(255, 255, 255, 0.96)',
  tooltipBorder: 'rgba(8, 145, 178, 0.2)',
  tooltipText: '#0f172a',
}

export function useChartTheme() {
  const { resolvedTheme } = useTheme()
  const colors = computed<ChartThemeColors>(() =>
    resolvedTheme.value === 'dark' ? dark : light
  )
  return { resolvedTheme, colors, isDark: computed(() => resolvedTheme.value === 'dark') }
}
