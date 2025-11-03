import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { tr } from 'date-fns/locale';

const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    action: '',
    status: '',
    username: '',
    search: ''
  });

  // API URL
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Audit logları fetch et
  const fetchAuditLogs = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        page: page,
        page_size: 50,
        ...filters
      });

      const response = await axios.get(`${API_URL}/api/audit-logs/?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setLogs(response.data.logs);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error('Audit logları yüklenemedi:', error);
      if (error.response?.status === 403) {
        alert('Bu sayfaya erişim yetkiniz yok!');
      }
    } finally {
      setLoading(false);
    }
  };

  // İstatistikleri fetch et
  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/audit-logs/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('İstatistikler yüklenemedi:', error);
    }
  };

  // CSV export
  const exportCSV = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/audit-logs/export/csv`, {
        headers: { Authorization: `Bearer ${token}` },
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
  }, [page, filters]);

  // Durum badge rengi
  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'success': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

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
      'mutabakat_delete': 'Mutabakat Silme',
      'user_create': 'Kullanıcı Oluşturma',
      'user_update': 'Kullanıcı Güncelleme',
      'user_delete': 'Kullanıcı Silme'
    };
    return translations[action] || action;
  };

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">📋 Audit Logs (Sistem Kayıtları)</h1>
        <button
          onClick={exportCSV}
          className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-2"
        >
          📥 CSV İndir
        </button>
      </div>

      {/* İstatistikler */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-gray-500 text-sm">Toplam Log</div>
            <div className="text-2xl font-bold">{stats.total_logs.toLocaleString('tr-TR')}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-gray-500 text-sm">Bugünkü Loglar</div>
            <div className="text-2xl font-bold text-blue-600">{stats.today_logs.toLocaleString('tr-TR')}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-gray-500 text-sm">Başarısız İşlemler</div>
            <div className="text-2xl font-bold text-red-600">{stats.failed_actions.toLocaleString('tr-TR')}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-gray-500 text-sm">Aktif Kullanıcılar</div>
            <div className="text-2xl font-bold text-green-600">{stats.unique_users.toLocaleString('tr-TR')}</div>
          </div>
        </div>
      )}

      {/* Filtreler */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="🔍 Arama..."
            className="border border-gray-300 rounded-lg px-3 py-2"
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          />
          <input
            type="text"
            placeholder="👤 Kullanıcı Adı"
            className="border border-gray-300 rounded-lg px-3 py-2"
            value={filters.username}
            onChange={(e) => setFilters({ ...filters, username: e.target.value })}
          />
          <select
            className="border border-gray-300 rounded-lg px-3 py-2"
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">Tüm Durumlar</option>
            <option value="success">Başarılı</option>
            <option value="failed">Başarısız</option>
            <option value="error">Hata</option>
          </select>
          <button
            onClick={() => setFilters({ action: '', status: '', username: '', search: '' })}
            className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-lg"
          >
            🔄 Filtreleri Temizle
          </button>
        </div>
      </div>

      {/* Tablo */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Yükleniyor...</div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">Kayıt bulunamadı</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tarih</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">İşlem</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Durum</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kullanıcı</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Şirket</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP Adresi</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Açıklama</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap">
                      {format(new Date(log.created_at), 'dd.MM.yyyy HH:mm:ss', { locale: tr })}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {translateAction(log.action)}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusBadgeColor(log.status)}`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">{log.username || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{log.company_name || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-500 font-mono">{log.ip_address || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 max-w-md truncate">
                      {log.action_description || '-'}
                      {log.error_message && (
                        <div className="text-red-500 text-xs mt-1">❌ {log.error_message}</div>
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
        <div className="flex justify-center items-center gap-2 mt-6">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-4 py-2 bg-gray-200 rounded-lg disabled:opacity-50"
          >
            ← Önceki
          </button>
          <span className="text-gray-600">
            Sayfa {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 bg-gray-200 rounded-lg disabled:opacity-50"
          >
            Sonraki →
          </button>
        </div>
      )}
    </div>
  );
};

export default AuditLogs;

