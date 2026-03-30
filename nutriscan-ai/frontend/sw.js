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


