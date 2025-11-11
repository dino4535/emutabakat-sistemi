import { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-toastify';

const API_URL = '/api';

/**
 * Push Notification Hook
 * Web Push Notification subscription yönetimi
 */
export const usePushNotification = () => {
  const [isSupported, setIsSupported] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscription, setSubscription] = useState(null);
  const [vapidPublicKey, setVapidPublicKey] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Browser desteği kontrolü
  useEffect(() => {
    if (
      'serviceWorker' in navigator &&
      'PushManager' in window &&
      'Notification' in window
    ) {
      setIsSupported(true);
      checkSubscriptionStatus();
    } else {
      setIsSupported(false);
      setLoading(false);
    }
  }, []);

  // VAPID public key'i al
  useEffect(() => {
    if (isSupported) {
      fetchVapidKey();
    }
  }, [isSupported]);

  const fetchVapidKey = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await fetch(`${API_URL}/push/status`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setVapidPublicKey(data.vapid_public_key);
        setIsSubscribed(data.enabled);
      }
    } catch (err) {
      console.error('VAPID key alınamadı:', err);
    } finally {
      setLoading(false);
    }
  };

  const checkSubscriptionStatus = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const sub = await registration.pushManager.getSubscription();
      
      if (sub) {
        setSubscription(sub);
        // Backend'de de var mı kontrol et
        const token = localStorage.getItem('token');
        if (token) {
          const response = await fetch(`${API_URL}/push/status`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          if (response.ok) {
            const data = await response.json();
            setIsSubscribed(data.enabled);
          }
        }
      } else {
        setIsSubscribed(false);
      }
    } catch (err) {
      console.error('Subscription durumu kontrol edilemedi:', err);
      setIsSubscribed(false);
    } finally {
      setLoading(false);
    }
  };

  // Push notification izni iste
  const requestPermission = async () => {
    if (!isSupported) {
      toast.error('Tarayıcınız push notification desteklemiyor');
      return false;
    }

    try {
      const permission = await Notification.requestPermission();
      
      if (permission === 'granted') {
        return true;
      } else if (permission === 'denied') {
        toast.error('Push notification izni reddedildi. Lütfen tarayıcı ayarlarından izin verin.');
        return false;
      } else {
        toast.warning('Push notification izni verilmedi');
        return false;
      }
    } catch (err) {
      console.error('İzin isteği hatası:', err);
      toast.error('İzin isteği başarısız');
      return false;
    }
  };

  // Push subscription oluştur
  const subscribe = useCallback(async () => {
    if (!isSupported || !vapidPublicKey) {
      toast.error('Push notification desteklenmiyor veya VAPID key bulunamadı');
      return false;
    }

    try {
      setLoading(true);
      setError(null);

      // İzin kontrolü
      const hasPermission = await requestPermission();
      if (!hasPermission) {
        setLoading(false);
        return false;
      }

      // Service Worker'ı kaydet
      const registration = await navigator.serviceWorker.register('/sw.js');
      await navigator.serviceWorker.ready;

      // Push subscription oluştur
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
      });

      // Backend'e kaydet
      const token = localStorage.getItem('token');
      if (!token) {
        toast.error('Oturum açmanız gerekiyor');
        setLoading(false);
        return false;
      }

      const response = await fetch(`${API_URL}/push/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          keys: {
            p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
            auth: arrayBufferToBase64(subscription.getKey('auth'))
          },
          user_agent: navigator.userAgent,
          device_info: `${navigator.platform} - ${navigator.userAgent}`
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Subscription kaydedilemedi');
      }

      setSubscription(subscription);
      setIsSubscribed(true);
      toast.success('Push notification aktif edildi! 🎉');
      setLoading(false);
      return true;

    } catch (err) {
      console.error('Subscription hatası:', err);
      setError(err.message);
      toast.error(`Push notification aktif edilemedi: ${err.message}`);
      setLoading(false);
      return false;
    }
  }, [isSupported, vapidPublicKey]);

  // Push subscription iptal et
  const unsubscribe = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      if (!subscription) {
        setLoading(false);
        return false;
      }

      // Backend'den sil
      const token = localStorage.getItem('token');
      if (token) {
        await fetch(`${API_URL}/push/unsubscribe?endpoint=${encodeURIComponent(subscription.endpoint)}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      }

      // Local subscription'ı iptal et
      await subscription.unsubscribe();

      setSubscription(null);
      setIsSubscribed(false);
      toast.success('Push notification devre dışı bırakıldı');
      setLoading(false);
      return true;

    } catch (err) {
      console.error('Unsubscribe hatası:', err);
      setError(err.message);
      toast.error(`Push notification devre dışı bırakılamadı: ${err.message}`);
      setLoading(false);
      return false;
    }
  }, [subscription]);

  // Test notification gönder
  const sendTestNotification = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        toast.error('Oturum açmanız gerekiyor');
        return;
      }

      const response = await fetch(`${API_URL}/push/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        toast.success('Test bildirimi gönderildi!');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Test bildirimi gönderilemedi');
      }
    } catch (err) {
      console.error('Test notification hatası:', err);
      toast.error(`Test bildirimi gönderilemedi: ${err.message}`);
    }
  };

  return {
    isSupported,
    isSubscribed,
    subscription,
    loading,
    error,
    subscribe,
    unsubscribe,
    sendTestNotification,
    vapidPublicKey
  };
};

// Helper functions
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

