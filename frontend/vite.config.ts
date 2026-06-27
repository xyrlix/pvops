import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// GitHub Pages serves project pages from /<repo>/. Allow overriding via
// VITE_BASE_PATH; defaults to '/' for local dev/Docker. When building for
// Pages, CI sets VITE_BASE_PATH automatically from ${{ github.repository }}.
function detectBase(env: Record<string, string>): string {
  if (env.VITE_BASE_PATH) return env.VITE_BASE_PATH
  if (process.env.GITHUB_REPOSITORY) {
    const repo = process.env.GITHUB_REPOSITORY.split('/')[1] || ''
    return repo ? `/${repo}/` : '/'
  }
  return '/'
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const base = detectBase(env)

  return {
    base,
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/ws': {
          target: 'ws://localhost:8000',
          ws: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      // 拆 vendor / echarts / element-plus 独立 chunk，配合路由懒分包
      // 降低首屏 index.js 体积（之前 ~2.3MB → 现在 ~600KB gzipped）。
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor-vue': ['vue', 'vue-router', 'pinia'],
            'vendor-echarts': ['echarts', 'vue-echarts'],
            'vendor-element': ['element-plus', '@element-plus/icons-vue'],
          },
          chunkFileNames: 'assets/[name]-[hash].js',
          entryFileNames: 'assets/[name]-[hash].js',
        },
      },
      chunkSizeWarningLimit: 800,  // 单 chunk > 800KB 才告警
    },
  }
})
