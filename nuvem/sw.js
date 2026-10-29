// Cache apenas dos arquivos públicos desta aplicação; dados de conta nunca são armazenados.
var VERSAO='atlas-financas-investimentos-19';
var PREFIXO='atlas-financas-investimentos-';
var ARQ=['./','./index.html','./investimentos.html','./documentos-core.js','./documentos.js','./manifest.webmanifest','./logo-financas.svg','./icone-192.png','./icone-512.png','./apple-touch-icon.png','./favicon-32.png'];
var PUBLICOS=ARQ.map(function(p){return new URL(p,self.registration.scope).href});
self.addEventListener('install',function(e){e.waitUntil(caches.open(VERSAO).then(function(c){return c.addAll(ARQ)}))});
self.addEventListener('activate',function(e){e.waitUntil(caches.keys().then(function(ks){return Promise.all(ks.filter(function(k){return k.indexOf(PREFIXO)===0&&k!==VERSAO}).map(function(k){return caches.delete(k)}))}).then(function(){return self.clients.claim()}))});
self.addEventListener('fetch',function(e){
  if(e.request.method!=='GET')return;
  var url=new URL(e.request.url);url.search='';url.hash='';
  if(PUBLICOS.indexOf(url.href)<0||e.request.headers.has('Authorization'))return;
  e.respondWith(fetch(e.request).then(function(r){if(r.ok&&r.type!=='opaque'){var c=r.clone();e.waitUntil(caches.open(VERSAO).then(function(x){return x.put(url.href,c)}))}return r}).catch(function(){return caches.open(VERSAO).then(function(c){return c.match(url.href)}).then(function(r){return r||Response.error()})}));
});


self.addEventListener('message',function(e){if(e.data&&e.data.type==='ATLAS_PRIVATE_DATA_POLICY'&&e.ports&&e.ports[0])e.ports[0].postMessage({privateResponsesCached:false,version:VERSAO})});
