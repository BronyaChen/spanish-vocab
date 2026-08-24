/*
 * Service Worker —— 西语单词 PWA
 * 缓存策略：
 *   - App Shell（/, /static/index.html, /static/manifest.json）→ Cache-First（离线可用）
 *   - API 请求（/api/*）→ Network-First，失败时回退缓存
 *   - 图片上传（/api/upload）→ Network-Only
 */
const CACHE_VERSION = 'v1';
const CACHE_NAME = `spanish-vocab-${CACHE_VERSION}`;

// 需要预缓存的 App Shell 资源
const APP_SHELL = [
  '/',
  '/static/index.html',
  '/static/manifest.json',
  '/static/icon-192.png',
  '/static/icon-512.png',
];

// ============================================================
// install：预缓存 App Shell，并立即激活新版本
// ============================================================
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

// ============================================================
// activate：清理旧版本缓存，接管所有客户端
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
// fetch：按路径分发不同缓存策略
// ============================================================
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // 仅处理 GET；其余（POST 等）直接走网络
  if (request.method !== 'GET') {
    return;
  }

  const url = new URL(request.url);

  // 仅处理同源请求，跨域直接放行
  if (url.origin !== self.location.origin) {
    return;
  }

  // 图片上传接口：Network-Only（不缓存，也不回退）
  if (url.pathname.startsWith('/api/upload')) {
    return; // 交给浏览器默认网络处理
  }

  // API 请求：Network-First，失败回退缓存
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // 其余（App Shell / 静态资源）：Cache-First
  event.respondWith(cacheFirst(request));
});

// Cache-First：命中缓存直接返回，否则请求网络并写入缓存
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    // 离线且无缓存时，尝试回退到首页 App Shell
    const fallback = await caches.match('/');
    if (fallback) {
      return fallback;
    }
    throw err;
  }
}

// Network-First：优先网络并更新缓存，失败时回退缓存
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
    if (cached) {
      return cached;
    }
    throw err;
  }
}
