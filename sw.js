const CACHE = 'jericho-v1';
const ASSETS = [
  '/JERICHO-AI/jericho.html',
  '/JERICHO-AI/manifest.json',
  '/JERICHO-AI/icons/icon-192.png',
  '/JERICHO-AI/icons/icon-512.png'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(clients.claim());
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  );
});
