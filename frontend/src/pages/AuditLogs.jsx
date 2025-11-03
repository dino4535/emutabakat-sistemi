import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { tr } from 'date-fns/locale';
import './AuditLogs.css';

const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({
    action: '',
    status: '',
    username: '',
    search: ''
  });

  // Audit logları fetch et
  const fetchAuditLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        page: page,
        page_size: 50,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== ''))
      });

      const response = await axios.get(`/api/audit-logs/?${params}`);

      setLogs(response.data.logs || []);
      setTotalPages(response.data.total_pages || 1);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Audit logları yüklenemedi:', error);
      setError(error.response?.data?.detail || 'Audit logları yüklenirken bir hata oluştu');
      if (error.response?.status === 403) {
        setError('Bu sayfaya erişim yetkiniz yok! Sadece admin kullanıcılar audit loglarını görüntüleyebilir.');
      }
    } finally {
      setLoading(false);
    }
  };

  // İstatistikleri fetch et
  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/audit-logs/stats');
      setStats(response.data);
    } catch (error) {
      console.error('İstatistikler yüklenemedi:', error);
    }
  };

  // CSV export
  const exportCSV = async () => {
    try {
      const response = await axios.get('/api/audit-logs/export/csv', {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit_logs_${format(new Date(), 'yyyyMMdd')}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('CSV export hatası:', error);
      alert('CSV export başarısız!');
    }
  };

  useEffect(() => {
    fetchAuditLogs();
    fetchStats();
  }, [page]);

  useEffect(() => {
    // Filtre değiştiğinde sayfa 1'e dön
    if (page === 1) {
      fetchAuditLogs();
    } else {
      setPage(1);
    }
  }, [filters]);

  // Durum badge rengi
  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'success': return 'badge-success';
      case 'failed': return 'badge-warning';
      case 'error': return 'badge-error';
      default: return 'badge-default';
    }
  };

  // Action türü Türkçe çeviri
  const translateAction = (action) => {
    const translations = {
      'login': '🔐 Giriş',
      'login_failed': '❌ Başarısız Giriş',
      'logout': '🚪 Çıkış',
      'password_change': '🔑 Şifre Değiştirme',
      'mutabakat_create': '📝 Mutabakat Oluşturma',
      'mutabakat_send': '📤 Mutabakat Gönderme',
      'mutabakat_approve': '✅ Mutabakat Onaylama',
      'mutabakat_reject': '❌ Mutabakat Reddetme',
      'mutabakat_delete': '🗑️ Mutabakat Silme',
      'mutabakat_view': '👁️ Mutabakat Görüntüleme',
      'mutabakat_download_pdf': '📥 PDF İndirme',
      'user_create': '👤 Kullanıcı Oluşturma',
      'user_update': '✏️ Kullanıcı Güncelleme',
      'user_delete': '🗑️ Kullanıcı Silme',
      'bayi_create': '🏪 Bayi Oluşturma',
      'bayi_update': '✏️ Bayi Güncelleme',
      'bayi_delete': '🗑️ Bayi Silme'
    };
    return translations[action] || action;
  };

  return (
    <div className="audit-logs-container">
      {/* Header */}
      <div className="audit-logs-header">
        <div className="header-title">
          <h1>📋 Audit Logs</h1>
          <p className="header-subtitle">Sistem Kayıtları ve Güvenlik Logları</p>
        </div>
        <button onClick={exportCSV} className="btn-export">
          📥 CSV İndir
        </button>
      </div>

      {/* İstatistikler */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card stat-primary">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-label">Toplam Log</div>
              <div className="stat-value">{stats.total_logs.toLocaleString('tr-TR')}</div>
            </div>
          </div>
          <div className="stat-card stat-info">
            <div className="stat-icon">📅</div>
            <div className="stat-content">
              <div className="stat-label">Bugünkü Loglar</div>
              <div className="stat-value">{stats.today_logs.toLocaleString('tr-TR')}</div>
            </div>
          </div>
          <div className="stat-card stat-danger">
            <div className="stat-icon">⚠️</div>
            <div className="stat-content">
              <div className="stat-label">Başarısız İşlemler</div>
              <div className="stat-value">{stats.failed_actions.toLocaleString('tr-TR')}</div>
            </div>
          </div>
          <div className="stat-card stat-success">
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <div className="stat-label">Aktif Kullanıcılar</div>
              <div className="stat-value">{stats.unique_users.toLocaleString('tr-TR')}</div>
            </div>
          </div>
        </div>
      )}

      {/* Filtreler */}
      <div className="filters-card">
        <div className="filters-grid">
          <input
            type="text"
            placeholder="🔍 Arama..."
            className="filter-input"
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          />
          <input
            type="text"
            placeholder="👤 Kullanıcı Adı"
            className="filter-input"
            value={filters.username}
            onChange={(e) => setFilters({ ...filters, username: e.target.value })}
          />
          <select
            className="filter-select"
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">Tüm Durumlar</option>
            <option value="success">✅ Başarılı</option>
            <option value="failed">⚠️ Başarısız</option>
            <option value="error">❌ Hata</option>
          </select>
          <button
            onClick={() => setFilters({ action: '', status: '', username: '', search: '' })}
            className="btn-reset"
          >
            🔄 Temizle
          </button>
        </div>
        {total > 0 && (
          <div className="filter-results">
            {total} kayıt bulundu
          </div>
        )}
      </div>

      {/* Hata Mesajı */}
      {error && (
        <div className="error-card">
          <div className="error-icon">⚠️</div>
          <div className="error-content">
            <h3>Hata</h3>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Tablo */}
      <div className="table-card">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Yükleniyor...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <h3>Kayıt Bulunamadı</h3>
            <p>Henüz audit log kaydı yok veya filtrelerinize uygun kayıt bulunamadı.</p>
            {Object.values(filters).some(v => v !== '') && (
              <button
                onClick={() => setFilters({ action: '', status: '', username: '', search: '' })}
                className="btn-clear-filters"
              >
                Filtreleri Temizle
              </button>
            )}
          </div>
        ) : (
          <div className="table-responsive">
            <table className="audit-table">
              <thead>
                <tr>
                  <th>Tarih</th>
                  <th>İşlem</th>
                  <th>Durum</th>
                  <th>Kullanıcı</th>
                  <th>Şirket</th>
                  <th>IP Adresi</th>
                  <th>Konum</th>
                  <th>Açıklama</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="table-row">
                    <td className="td-date">
                      {format(new Date(log.created_at), 'dd.MM.yyyy', { locale: tr })}
                      <br />
                      <span className="time-text">
                        {format(new Date(log.created_at), 'HH:mm:ss', { locale: tr })}
                      </span>
                    </td>
                    <td className="td-action">
                      {translateAction(log.action)}
                    </td>
                    <td>
                      <span className={`badge ${getStatusBadgeColor(log.status)}`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="td-user">{log.username || '-'}</td>
                    <td className="td-company">{log.company_name || '-'}</td>
                    <td className="td-ip">{log.ip_address || '-'}</td>
                    <td className="td-location">
                      {log.city ? `${log.city}, ${log.country}` : '-'}
                      {log.isp && <div className="isp-text">{log.isp}</div>}
                    </td>
                    <td className="td-description">
                      {log.action_description || '-'}
                      {log.error_message && (
                        <div className="error-message">❌ {log.error_message}</div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Sayfalama */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="btn-page"
          >
            ← Önceki
          </button>
          <span className="page-info">
            Sayfa {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="btn-page"
          >
            Sonraki →
          </button>
        </div>
      )}
    </div>
  );
};

export default AuditLogs;
