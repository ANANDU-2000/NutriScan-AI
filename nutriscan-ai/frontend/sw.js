/* Basic service worker for NutriScan notifications */

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  if (!event.data) return;
  let data = {};
  try {
    data = event.data.json();
  } catch (e) {
    data = { title: 'NutriScan', body: event.data.text() };
  }
  const title = data.title || 'NutriScan';
  const body = data.body || '';
  const options = {
    body,
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    data: data.payload || {},
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientsArr) => {
      for (const client of clientsArr) {
        if ('focus' in client) {
          client.focus();
          return;
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow('/');
      }
    })
  );
});

const CACHE_STATIC = 'nutriscan-static-v2';
const SHELL = ['/'];

// Cache basic shell assets, but never permanently cache HTML — always prefer network
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_STATIC).then((cache) => cache.addAll(SHELL)),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_STATIC)
          .map((key) => caches.delete(key)),
      ),
    ),
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;

  // For navigations (HTML pages), always try network first so updated index.html loads
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match('/index.html') || caches.match('/')),
    );
    return;
  }

  // For static assets (CSS, JS, images), use cache-first
  event.respondWith(
    caches.match(request).then((response) => response || fetch(request)),
  );
});


