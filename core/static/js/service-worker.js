/* Service Worker for Share A Hobby PWA */
const APP_VERSION = 'v1';
const PRECACHE = `precache-${APP_VERSION}`;
const RUNTIME = `runtime-${APP_VERSION}`;
const OFFLINE_URL = '/static/offline.html';

// Core assets to pre-cache (add more static assets as needed)
const PRECACHE_URLS = [
  '/',
  OFFLINE_URL,
  '/static/css/custom.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(PRECACHE).then(cache => cache.addAll(PRECACHE_URLS)).then(self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => ![PRECACHE, RUNTIME].includes(k)).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

// Strategy helpers
async function networkFirst(request) {
  try {
    const fresh = await fetch(request);
    const cache = await caches.open(RUNTIME);
    cache.put(request, fresh.clone());
    return fresh;
  } catch (e) {
    const cache = await caches.match(request);
    return cache || caches.match(OFFLINE_URL);
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(RUNTIME);
  const cached = await cache.match(request);
  const networkPromise = fetch(request).then(resp => {
    cache.put(request, resp.clone());
    return resp;
  }).catch(() => undefined);
  return cached || networkPromise || caches.match(OFFLINE_URL);
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  // Only handle GET
  if (request.method !== 'GET') return;

  // API calls: network first
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/admin/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // HTML navigations: network first (for fresh content) with offline fallback
  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request));
    return;
  }

  // Static assets: stale-while-revalidate
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // Default: try cache, then network, then offline
  event.respondWith(
    caches.match(request).then(cached => cached || fetch(request).catch(() => caches.match(OFFLINE_URL)))
  );
});
