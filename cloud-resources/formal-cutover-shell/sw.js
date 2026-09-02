const SHERLOCK_PREFIX = '/sherlock-english/'
const MIGRATION_URL = 'https://summertxia0306-hue.github.io/sherlock-english/'

self.addEventListener('install', () => self.skipWaiting())

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    for (const name of await caches.keys()) {
      const cache = await caches.open(name)
      for (const request of await cache.keys()) {
        const url = new URL(request.url)
        if (url.origin === self.location.origin && url.pathname.startsWith(SHERLOCK_PREFIX)) {
          await cache.delete(request)
        }
      }
    }
    await self.clients.claim()
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true })
    await Promise.all(windows
      .filter((client) => new URL(client.url).pathname.startsWith(SHERLOCK_PREFIX))
      .map((client) => client.navigate(MIGRATION_URL)))
  })())
})

self.addEventListener('fetch', (event) => {
  if (event.request.mode !== 'navigate') return
  const url = new URL(event.request.url)
  if (url.origin !== self.location.origin || !url.pathname.startsWith(SHERLOCK_PREFIX)) return
  event.respondWith(fetch(event.request, { cache: 'no-store' }))
})
