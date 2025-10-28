import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { 
  FaCheck, 
  FaTimes, 
  FaPaperPlane, 
  FaFileAlt,
  FaClock
} from 'react-icons/fa'
import './RecentActivities.css'

/**
 * Recent Activities Component
 * Son aktiviteleri timeline olarak gösterir
 */
export default function RecentActivities() {
  const { data: notifications, isLoading } = useQuery({
    queryKey: ['recent-notifications'],
    queryFn: async () => {
      const response = await axios.get('/api/notifications/')
      return response.data.slice(0, 5) // Son 5 aktivite
    },
    refetchInterval: 30000 // 30 saniyede bir yenile
  })

  const getActivityIcon = (type) => {
    switch(type) {
      case 'approved':
        return <FaCheck className="activity-icon success" />
      case 'rejected':
        return <FaTimes className="activity-icon danger" />
      case 'pending_approval':
      case 'waiting_approval':
        return <FaClock className="activity-icon warning" />
      case 'draft':
        return <FaFileAlt className="activity-icon info" />
      default:
        return <FaFileAlt className="activity-icon default" />
    }
  }

  const formatTimeAgo = (dateString) => {
    if (!dateString) return 'Bilinmiyor'
    
    try {
      const now = new Date()
      const date = new Date(dateString)
      
      // Invalid date kontrolü
      if (isNaN(date.getTime())) {
        return 'Bilinmiyor'
      }
      
      const seconds = Math.floor((now - date) / 1000)

      if (seconds < 60) return 'Az önce'
      if (seconds < 3600) return `${Math.floor(seconds / 60)} dakika önce`
      if (seconds < 86400) return `${Math.floor(seconds / 3600)} saat önce`
      if (seconds < 604800) return `${Math.floor(seconds / 86400)} gün önce`
      
      return date.toLocaleDateString('tr-TR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
      })
    } catch (error) {
      console.error('Tarih format hatası:', error, dateString)
      return 'Bilinmiyor'
    }
  }

  if (isLoading) {
    return (
      <div className="recent-activities">
        <h3 className="recent-activities-title">📋 Son Aktiviteler</h3>
        <div className="activities-loading">
          {[1, 2, 3].map((i) => (
            <div key={i} className="activity-skeleton">
              <div className="skeleton-icon"></div>
              <div className="skeleton-content">
                <div className="skeleton-text"></div>
                <div className="skeleton-time"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!notifications || notifications.length === 0) {
    return (
      <div className="recent-activities">
        <h3 className="recent-activities-title">📋 Son Aktiviteler</h3>
        <div className="activities-empty">
          <FaClock className="empty-icon" />
          <p>Henüz aktivite bulunmuyor</p>
        </div>
      </div>
    )
  }

  return (
    <div className="recent-activities">
      <h3 className="recent-activities-title">📋 Son Aktiviteler</h3>
      <div className="activities-timeline">
        {notifications.map((notification, index) => (
          <div key={notification.id || index} className="activity-item">
            <div className="activity-icon-wrapper">
              {getActivityIcon(notification.type)}
              {index < notifications.length - 1 && <div className="activity-line"></div>}
            </div>
            <div className="activity-content">
              <p className="activity-message">{notification.message}</p>
              <span className="activity-time">{formatTimeAgo(notification.date)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

