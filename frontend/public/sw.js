/**
 * Service Worker - Push Notifications için
 * Bu dosya public klasöründe olmalı (root seviyesinde)
 */

const CACHE_NAME = 'emutabakat-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/favicon.ico'
];

// Install event - Cache oluştur
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Cache açıldı');
        return cache.addAll(urlsToCache);
      })
  );
});

// Activate event - Eski cache'leri temizle
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Eski cache siliniyor:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch event - Cache'den veya network'ten getir
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Cache'de varsa cache'den dön
        if (response) {
          return response;
        }
        // Yoksa network'ten getir
        return fetch(event.request);
      })
  );
});

// Push event - Push notification geldiğinde
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification alındı:', event);
  
  let notificationData = {
    title: 'E-Mutabakat',
    body: 'Yeni bildirim',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    tag: 'default',
    data: {}
  };
  
  // Push data varsa parse et
  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = {
        title: data.title || notificationData.title,
        body: data.body || notificationData.body,
        icon: data.icon || notificationData.icon,
        badge: data.badge || notificationData.badge,
        tag: data.tag || notificationData.tag,
        requireInteraction: data.requireInteraction || false,
        silent: data.silent || false,
        data: data.data || {}
      };
    } catch (e) {
      console.error('[SW] Push data parse hatası:', e);
      // Text olarak al
      notificationData.body = event.data.text();
    }
  }
  
  // Notification göster
  event.waitUntil(
    self.registration.showNotification(notificationData.title, {
      body: notificationData.body,
      icon: notificationData.icon,
      badge: notificationData.badge,
      tag: notificationData.tag,
      requireInteraction: notificationData.requireInteraction,
      silent: notificationData.silent,
      data: notificationData.data,
      vibrate: notificationData.silent ? [] : [200, 100, 200],
      actions: [
        {
          action: 'open',
          title: 'Aç'
        },
        {
          action: 'close',
          title: 'Kapat'
        }
      ]
    })
  );
});

// Notification click event - Kullanıcı bildirime tıkladığında
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification tıklandı:', event);
  
  event.notification.close();
  
  // Action'a göre işlem yap
  if (event.action === 'close') {
    return;
  }
  
  // Data'da link varsa aç
  const data = event.notification.data || {};
  let url = '/';
  
  if (data.type === 'mutabakat_approved' || data.type === 'mutabakat_rejected' || data.type === 'mutabakat_sent') {
    // Mutabakat detay sayfasına git
    url = `/mutabakat?search=${data.mutabakat_no || ''}`;
  } else if (data.link) {
    url = data.link;
  }
  
  // Client'ı aç
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Açık bir window varsa focus et
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i];
          if (client.url === url && 'focus' in client) {
            return client.focus();
          }
        }
        // Yoksa yeni window aç
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
  );
});

// Notification close event
self.addEventListener('notificationclose', (event) => {
  console.log('[SW] Notification kapatıldı:', event);
});

