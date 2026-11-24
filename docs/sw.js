// Diocese Finder service worker: keeps the whole app on the device so it opens offline.
// The version below changes automatically whenever build.py produces a new index.html,
// so phones pick up updated bishop lists the next time they open the app with a signal.
const VERSION = "84611507fd8b";
const CACHE = "diocese-finder-" + VERSION;
const FILES = ["./", "./index.html", "./manifest.webmanifest",
  "./icons/icon-180.png", "./icons/icon-192.png", "./icons/icon-512.png", "./icons/icon-maskable-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k.startsWith("diocese-finder-") && k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(hit =>
      hit || fetch(req).catch(() => req.mode === "navigate" ? caches.match("./index.html") : Response.error())
    )
  );
});
