import React, { useState } from 'react';
import { usePushNotification } from '../hooks/usePushNotification';
import { FaBell, FaBellSlash, FaSpinner } from 'react-icons/fa';
import { toast } from 'react-toastify';
import './PushNotificationButton.css';

/**
 * Push Notification Button Component
 * Push notification'ları aktif/pasif etmek için buton
 */
export default function PushNotificationButton() {
  const {
    isSupported,
    isSubscribed,
    loading,
    subscribe,
    unsubscribe,
    sendTestNotification
  } = usePushNotification();

  const [testing, setTesting] = useState(false);

  const handleToggle = async () => {
    if (isSubscribed) {
      await unsubscribe();
    } else {
      await subscribe();
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      await sendTestNotification();
    } finally {
      setTesting(false);
    }
  };

  if (!isSupported) {
    return (
      <div className="push-notification-button unsupported">
        <FaBellSlash />
        <span>Push notification desteklenmiyor</span>
      </div>
    );
  }

  return (
    <div className="push-notification-button">
      <button
        className={`btn-push-toggle ${isSubscribed ? 'active' : 'inactive'}`}
        onClick={handleToggle}
        disabled={loading}
      >
        {loading ? (
          <><FaSpinner className="spinner" /> Yükleniyor...</>
        ) : isSubscribed ? (
          <><FaBell /> Bildirimler Açık</>
        ) : (
          <><FaBellSlash /> Bildirimler Kapalı</>
        )}
      </button>
      
      {isSubscribed && (
        <button
          className="btn-push-test"
          onClick={handleTest}
          disabled={testing}
        >
          {testing ? (
            <><FaSpinner className="spinner" /> Test ediliyor...</>
          ) : (
            '🧪 Test Bildirimi'
          )}
        </button>
      )}
    </div>
  );
}

