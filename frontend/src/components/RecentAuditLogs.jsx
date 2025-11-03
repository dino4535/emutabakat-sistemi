import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { format } from 'date-fns'
import { tr } from 'date-fns/locale'
import { FaHistory, FaCheckCircle, FaExclamationCircle, FaTimesCircle } from 'react-icons/fa'

export default function RecentAuditLogs() {
  const { data: auditLogs, isLoading } = useQuery({
    queryKey: ['recent-audit-logs'],
    queryFn: async () => {
      try {
        const response = await axios.get('/api/audit-logs/?page=1&page_size=5')
        return response.data.logs || []
      } catch (error) {
        console.error('Audit logs yüklenemedi:', error)
        return []
      }
    },
    refetchInterval: 60000, // 1 dakikada bir yenile
    retry: false // 403 hatası alınca tekrar deneme
  })

  // Durum ikonu
  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <FaCheckCircle style={{ color: '#10b981' }} />
      case 'failed':
        return <FaExclamationCircle style={{ color: '#f59e0b' }} />
      case 'error':
        return <FaTimesCircle style={{ color: '#ef4444' }} />
      default:
        return <FaHistory style={{ color: '#6b7280' }} />
    }
  }

  // Action türü Türkçe çeviri
  const translateAction = (action) => {
    const translations = {
      'login': 'Giriş',
      'login_failed': 'Başarısız Giriş',
      'logout': 'Çıkış',
      'mutabakat_create': 'Mutabakat Oluşturma',
      'mutabakat_send': 'Mutabakat Gönderme',
      'mutabakat_approve': 'Mutabakat Onaylama',
      'mutabakat_reject': 'Mutabakat Reddetme',
      'user_create': 'Kullanıcı Oluşturma',
      'user_update': 'Kullanıcı Güncelleme'
    }
    return translations[action] || action
  }

  if (isLoading) {
    return (
      <div className="recent-activities card">
        <div className="card-header">
          <h3>
            <FaHistory /> Son Sistem Logları
          </h3>
        </div>
        <div className="card-body">
          <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
            Yükleniyor...
          </div>
        </div>
      </div>
    )
  }

  if (!auditLogs || auditLogs.length === 0) {
    return (
      <div className="recent-activities card">
        <div className="card-header">
          <h3>
            <FaHistory /> Son Sistem Logları
          </h3>
          <Link to="/audit-logs" className="view-all-link">
            Tümünü Gör →
          </Link>
        </div>
        <div className="card-body">
          <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
            Henüz audit log kaydı yok veya görüntüleme yetkiniz yok.
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="recent-activities card">
      <div className="card-header">
        <h3>
          <FaHistory /> Son Sistem Logları
        </h3>
        <Link to="/audit-logs" className="view-all-link">
          Tümünü Gör →
        </Link>
      </div>
      <div className="card-body">
        <div className="activities-list">
          {auditLogs.map((log) => (
            <div key={log.id} className="activity-item">
              <div className="activity-icon">
                {getStatusIcon(log.status)}
              </div>
              <div className="activity-content">
                <div className="activity-title">
                  <strong>{translateAction(log.action)}</strong>
                  {log.username && <span className="activity-user"> - {log.username}</span>}
                </div>
                <div className="activity-description">
                  {log.action_description || 'İşlem gerçekleştirildi'}
                </div>
                <div className="activity-meta">
                  <span className="activity-time">
                    {format(new Date(log.created_at), 'dd.MM.yyyy HH:mm', { locale: tr })}
                  </span>
                  {log.ip_address && (
                    <span className="activity-ip"> • IP: {log.ip_address}</span>
                  )}
                  {log.city && (
                    <span className="activity-location"> • {log.city}</span>
                  )}
                </div>
                {log.error_message && (
                  <div className="activity-error">
                    ❌ {log.error_message}
                  </div>
                )}
              </div>
              <div className={`activity-status status-${log.status}`}>
                {log.status}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

