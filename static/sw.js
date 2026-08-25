/*
 * Service Worker —— 西语单词 PWA (纯前端版)
 * 缓存策略：Network-First（所有请求）
 * 离线时回退缓存，确保鸿蒙浏览器兼容性
 */
const CACHE_VERSION = 'v2';
const CACHE_NAME = `spanish-vocab-${CACHE_VERSION}`;

// 预缓存资源（相对路径）
const APP_SHELL = [
  './',
  './index.html',
  './seed.json',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
];

// ============================================================
// install：预缓存 App Shell，立即激活
// ============================================================
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

// ============================================================
// activate：清理旧缓存，接管客户端
// ============================================================
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ============================================================
// fetch：Network-First 策略（所有 GET 请求）
// 非 GET 请求和跨域请求直接放行
// ============================================================
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // 仅处理 GET 请求
  if (request.method !== 'GET') return;

  // 跨域请求直接放行（如 CF Worker OCR 调用）
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Network-First：优先网络，失败时回退缓存
  event.respondWith(networkFirst(request));
});

async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    // 离线且无缓存时，尝试回退首页
    const fallback = await cache.match('./index.html');
    if (fallback) return fallback;
    throw err;
  }
}
