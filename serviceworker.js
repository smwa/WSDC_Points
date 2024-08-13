const cacheName = 'static_site_cache_v1';

const reloadedAssets = {};

self.addEventListener("install", (event) => {});

self.addEventListener('fetch', (event) => {
  const url = event.request.url;
  event.respondWith(caches.open(cacheName).then((cache) => {
    return cache.match(event.request).then((cachedResponse) => {
      let fetchedResponse = null;
      if (!cachedResponse || !(url in reloadedAssets)) {
        fetchedResponse = fetch(event.request).then(async (networkResponse) => {
          cache.put(event.request, networkResponse.clone());

          reloadedAssets[url] = true;
          const client = await self.clients.get(event.clientId);
          if (client && cachedResponse.headers.get('last-modified') !== networkResponse.headers.get('last-modified')) {
            client.postMessage({
              type: "fetched",
              url: url,
            });
          }
          
          return networkResponse;
        });

      }

      return cachedResponse || fetchedResponse;
    });
  }));
});
