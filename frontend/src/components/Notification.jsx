import { useState, useEffect } from 'react'
import { FaCheckCircle, FaExclamationCircle, FaInfoCircle, FaTimes } from 'react-icons/fa'
import './Notification.css'

let showNotificationGlobal = null

export function Notification() {
  const [notifications, setNotifications] = useState([])

  useEffect(() => {
    showNotificationGlobal = (message, type = 'success', duration = 5000) => {
      const id = Date.now()
      const notification = { id, message, type, duration }
      
      setNotifications(prev => [...prev, notification])
      
      // Auto remove
      if (duration > 0) {
        setTimeout(() => {
          removeNotification(id)
        }, duration)
      }
    }
  }, [])

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <FaCheckCircle />
      case 'error':
        return <FaExclamationCircle />
      case 'info':
        return <FaInfoCircle />
      default:
        return <FaInfoCircle />
    }
  }

  return (
    <div className="notification-container">
      {notifications.map(notification => (
        <div 
          key={notification.id} 
          className={`notification notification-${notification.type}`}
        >
          <div className="notification-icon">
            {getIcon(notification.type)}
          </div>
          <div className="notification-message">
            {notification.message}
          </div>
          <button 
            className="notification-close"
            onClick={() => removeNotification(notification.id)}
          >
            <FaTimes />
          </button>
        </div>
      ))}
    </div>
  )
}

// Global function to show notifications
export const showNotification = (message, type = 'success', duration = 5000) => {
  if (showNotificationGlobal) {
    showNotificationGlobal(message, type, duration)
  }
}

