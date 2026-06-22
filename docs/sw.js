const CACHE='finanalysis-v1';
const URLS=["./", "./latest_report.html", "./share/", "./share/000002.SZ.html", "./share/0700.HK.html", "./share/0981.HK.html", "./share/2007.HK.html", "./share/2696.HK.html", "./share/601398.SH.html", "./share/OXY.html", "./private/latest_report.html"];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(URLS)).catch(()=>undefined));self.skipWaiting();});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))));self.clients.claim();});
self.addEventListener('fetch',event=>{if(event.request.method!=='GET')return;event.respondWith(fetch(event.request).then(response=>{const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy));return response;}).catch(()=>caches.match(event.request).then(cached=>cached||caches.match('./'))));});
