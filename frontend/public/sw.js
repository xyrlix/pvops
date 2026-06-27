/**
 * PVOps Service Worker —— 最小化版本：
 * - 静态资源：cache-first（vite hashed assets 永不变）
 * - API GET 请求：network-first，回退到 cache
 * - API POST/PUT/PATCH：永不缓存
 * - 不支持时降级到 pass-through
 *
 * 注册位置：main.ts（仅在 HTTPS / localhost 下生效）
 */

const CACHE_VERSION = 'pvops-v1'
const STATIC_CACHE = `${CACHE_VERSION}-static`
const API_CACHE = `${CACHE_VERSION}-api`

const STATIC_PATHS = ['/', '/index.html', '/manifest.webmanifest']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(STATIC_PATHS).catch(() => {}))
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => !k.startsWith(CACHE_VERSION))
          .map((k) => caches.delete(k))
      )
    )
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const req = event.request
  const url = new URL(req.url)

  // 1. 写操作 / 跨域 — 直接放行
  if (req.method !== 'GET' || url.origin !== self.location.origin) {
    return
  }

  // 2. /api/* — network-first，回退到 cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(req)
        .then((resp) => {
          if (resp.ok) {
            const clone = resp.clone()
            caches.open(API_CACHE).then((c) => c.put(req, clone)).catch(() => {})
          }
          return resp
        })
        .catch(() => caches.match(req).then((cached) => cached || new Response('offline', { status: 503 })))
    )
    return
  }

  // 3. 静态资源（vite hashed assets）— cache-first
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached
      return fetch(req).then((resp) => {
        if (resp.ok && (url.pathname.startsWith('/assets/') || STATIC_PATHS.includes(url.pathname))) {
          const clone = resp.clone()
          caches.open(STATIC_CACHE).then((c) => c.put(req, clone)).catch(() => {})
        }
        return resp
      }).catch(() => caches.match('/index.html').then((r) => r || new Response('offline', { status: 503 })))
    })
  )
})