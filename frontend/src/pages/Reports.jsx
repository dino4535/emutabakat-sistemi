import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { 
  FaChartLine, FaUsers, FaFileInvoice, FaCheckCircle, FaTimesCircle, 
  FaClock, FaTrophy, FaFilter, FaSearch, FaChartBar, FaTable, FaFire, 
  FaDownload, FaCalendarAlt 
} from 'react-icons/fa'
import './Reports.css'

export default function Reports() {
  const [activeTab, setActiveTab] = useState('overview') // overview, detailed, period, heatmap, trends, dayhour
  const [filters, setFilters] = useState({
    userId: '',
    period: ''
  })
  const [heatmapDays, setHeatmapDays] = useState(30)
  const [trendDays, setTrendDays] = useState(90)
  const [trendGroupBy, setTrendGroupBy] = useState('day') // day | week
  const [dayHourDays, setDayHourDays] = useState(30)
  const [exportPeriod, setExportPeriod] = useState('') // Excel export için dönem seçimi

  // Genel istatistikler
  const { data: overview } = useQuery({
    queryKey: ['reports-overview'],
    queryFn: async () => {
      const response = await axios.get('/api/reports/overview')
      return response.data
    }
  })

  // Onay istatistikleri
  const { data: approvalStats } = useQuery({
    queryKey: ['reports-approval-stats'],
    queryFn: async () => {
      const response = await axios.get('/api/reports/approval-statistics')
      return response.data
    }
  })

  // Mevcut dönemler (dropdown için)
  const { data: availablePeriods } = useQuery({
    queryKey: ['reports-available-periods'],
    queryFn: async () => {
      const response = await axios.get('/api/reports/available-periods')
      return response.data
    }
  })

  // Detaylı kullanıcı analizi (filtreli)
  const { data: detailedAnalysis, refetch: refetchDetailed } = useQuery({
    queryKey: ['reports-detailed-analysis', filters],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (filters.userId) params.append('user_id', filters.userId)
      if (filters.period) params.append('period', filters.period)
      
      const response = await axios.get(`/api/reports/detailed-user-analysis?${params}`)
      return response.data
    }
  })

  // Dönemsel karşılaştırma (seçilen döneme göre son 12 ay)
  const [comparisonPeriod, setComparisonPeriod] = useState('')
  const { data: periodComparison } = useQuery({
    queryKey: ['reports-period-comparison', comparisonPeriod],
    queryFn: async () => {
      const qs = comparisonPeriod ? `?end_period=${comparisonPeriod}` : ''
      const response = await axios.get(`/api/reports/period-comparison${qs}`)
      return response.data
    }
  })

  // Bekleyen mutabakat ısı haritası
  const { data: heatmapData } = useQuery({
    queryKey: ['reports-pending-heatmap', heatmapDays],
    queryFn: async () => {
      const response = await axios.get(`/api/reports/pending-heatmap?days=${heatmapDays}`)
      return response.data
    }
  })

  // Trend grafikleri (zaman serisi)
  const { data: timeSeriesData } = useQuery({
    queryKey: ['reports-time-series', trendDays, trendGroupBy],
    queryFn: async () => {
      const response = await axios.get(`/api/reports/time-series?days=${trendDays}&group_by=${trendGroupBy}`)
      return response.data
    }
  })

  // Gün-saat ısı haritası
  const { data: dayHourData } = useQuery({
    queryKey: ['reports-day-hour-heatmap', dayHourDays],
    queryFn: async () => {
      const response = await axios.get(`/api/reports/day-hour-heatmap?days=${dayHourDays}`)
      return response.data
    }
  })

  // Kullanıcı listesi (filtre için)
  const { data: users } = useQuery({
    queryKey: ['users-list'],
    queryFn: async () => {
      const response = await axios.get('/api/auth/users')
      return response.data.filter(u => ['admin', 'muhasebe', 'planlama'].includes(u.role))
    }
  })

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY'
    }).format(amount || 0)
  }

  const getRoleText = (role) => {
    const roles = {
      'admin': 'Admin',
      'muhasebe': 'Muhasebe',
      'planlama': 'Planlama',
      'musteri': 'Müşteri',
      'tedarikci': 'Tedarikçi'
    }
    return roles[role] || role
  }

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }))
  }

  const clearFilters = () => {
    setFilters({ userId: '', period: '' })
  }

  const handleExportCSV = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/reports/time-series/export.csv?days=${trendDays}&group_by=${trendGroupBy}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!response.ok) throw new Error('Export failed')
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `trend-raporu-${trendDays}gun-${trendGroupBy}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('CSV export hatası:', error)
      alert('CSV export başarısız oldu')
    }
  }

  const handleExportExcel = async () => {
    try {
      const token = localStorage.getItem('token')
      const params = new URLSearchParams()
      if (exportPeriod) {
        params.append('period', exportPeriod)
      }
      
      const response = await fetch(`/api/reports/mutabakat-list/export.xlsx?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) throw new Error('Export failed')
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const periodStr = exportPeriod ? exportPeriod.replace('/', '-') : 'tum-donemler'
      a.download = `mutabakat-listesi-${periodStr}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Excel export hatası:', error)
      alert('Excel export başarısız oldu')
    }
  }

  return (
    <div className="reports-page">
      <div className="page-header">
        <div>
          <h1><FaChartLine /> Raporlar ve Analizler</h1>
          <p>Detaylı istatistikler ve performans analizleri</p>
        </div>
      </div>

      {/* Sekmeler */}
      <div className="tabs-container">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <FaChartBar /> Genel Bakış
        </button>
        <button 
          className={`tab ${activeTab === 'detailed' ? 'active' : ''}`}
          onClick={() => setActiveTab('detailed')}
        >
          <FaTable /> Detaylı Analiz
        </button>
        <button 
          className={`tab ${activeTab === 'period' ? 'active' : ''}`}
          onClick={() => setActiveTab('period')}
        >
          <FaChartLine /> Dönemsel Karşılaştırma
        </button>
        <button 
          className={`tab ${activeTab === 'heatmap' ? 'active' : ''}`}
          onClick={() => setActiveTab('heatmap')}
        >
          <FaFire /> Bekleyen Mutabakat Isı Haritası
        </button>
        <button 
          className={`tab ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          <FaChartLine /> Trend Grafikleri
        </button>
        <button 
          className={`tab ${activeTab === 'dayhour' ? 'active' : ''}`}
          onClick={() => setActiveTab('dayhour')}
        >
          <FaCalendarAlt /> Gün-Saat Isı Haritası
        </button>
      </div>

      {/* Genel Bakış Sekmesi */}
      {activeTab === 'overview' && (
        <div className="tab-content">
          {/* Excel Export Bölümü */}
          <div className="stats-section">
            <h2>Mutabakat Listesi Excel Export</h2>
            <div className="export-panel">
              <div className="export-controls">
                <label>Dönem Seçin (Opsiyonel):</label>
                <select 
                  value={exportPeriod} 
                  onChange={(e) => setExportPeriod(e.target.value)}
                  className="export-select"
                >
                  <option value="">Tüm Dönemler</option>
                  {availablePeriods?.map(period => (
                    <option key={period} value={period}>
                      {period}
                    </option>
                  ))}
                </select>
                <button 
                  className="btn btn-primary" 
                  onClick={handleExportExcel}
                  style={{marginLeft: '16px'}}
                >
                  <FaDownload /> Excel İndir
                </button>
              </div>
              <p style={{color: 'var(--text-secondary)', marginTop: '8px', fontSize: '14px'}}>
                Seçilen döneme ait mutabakat listesini Excel formatında indirebilirsiniz. 
                Alıcının VKN'si dahil tüm detaylar export edilecektir.
              </p>
            </div>
          </div>

          {/* Genel İstatistikler */}
          {overview && (
            <div className="stats-section">
              <h2>Genel Durum</h2>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon blue">
                    <FaUsers />
                  </div>
                  <div className="stat-details">
                    <h3>{overview.users.total}</h3>
                    <p>Toplam Kullanıcı</p>
                    <small>{overview.users.active} aktif</small>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon green">
                    <FaFileInvoice />
                  </div>
                  <div className="stat-details">
                    <h3>{overview.mutabakats.total}</h3>
                    <p>Toplam Mutabakat</p>
                    <small>{overview.mutabakats.recent_30_days} son 30 gün</small>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon orange">
                    <FaChartLine />
                  </div>
                  <div className="stat-details">
                    <h3>{formatCurrency(overview.financial.total_borc)}</h3>
                    <p>Toplam Borç</p>
                    <small>Onaylanmış</small>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon purple">
                    <FaChartLine />
                  </div>
                  <div className="stat-details">
                    <h3>{formatCurrency(overview.financial.total_alacak)}</h3>
                    <p>Toplam Alacak</p>
                    <small>Onaylanmış</small>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Onay İstatistikleri */}
          {approvalStats && (
            <div className="stats-section">
              <h2>Onay/Red Durumu</h2>
              <div className="approval-stats">
                <div className="approval-card">
                  <FaCheckCircle className="icon success" />
                  <div className="info">
                    <h3>{approvalStats.approved}</h3>
                    <p>Onaylanan</p>
                    <div className="progress-bar">
                      <div 
                        className="progress success" 
                        style={{width: `${approvalStats.approval_rate}%`}}
                      ></div>
                    </div>
                    <small>{approvalStats.approval_rate}% onay oranı</small>
                  </div>
                </div>

                <div className="approval-card">
                  <FaTimesCircle className="icon danger" />
                  <div className="info">
                    <h3>{approvalStats.rejected}</h3>
                    <p>Reddedilen</p>
                    <div className="progress-bar">
                      <div 
                        className="progress danger" 
                        style={{width: `${approvalStats.rejection_rate}%`}}
                      ></div>
                    </div>
                    <small>{approvalStats.rejection_rate}% red oranı</small>
                  </div>
                </div>

                <div className="approval-card">
                  <FaClock className="icon warning" />
                  <div className="info">
                    <h3>{approvalStats.pending}</h3>
                    <p>Bekleyen</p>
                    <small>Yanıt bekliyor</small>
                  </div>
                </div>

                <div className="approval-card">
                  <FaChartLine className="icon info" />
                  <div className="info">
                    <h3>{approvalStats.avg_response_time_days} gün</h3>
                    <p>Ort. Yanıt Süresi</p>
                    <small>Onaylananlar için</small>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detaylı Analiz Sekmesi */}
      {activeTab === 'detailed' && (
        <div className="tab-content">
          {/* Filtreler */}
          <div className="filter-panel">
            <h3><FaFilter /> Filtreler</h3>
            <div className="filter-row">
              <div className="filter-item">
                <label>Kullanıcı</label>
                <select 
                  value={filters.userId} 
                  onChange={(e) => handleFilterChange('userId', e.target.value)}
                >
                  <option value="">Tüm Kullanıcılar</option>
                  {users?.map(user => (
                    <option key={user.id} value={user.id}>
                      {user.company_name || user.full_name || user.username}
                    </option>
                  ))}
                </select>
              </div>

              <div className="filter-item">
                <label>Dönem (Mutabakat Bitiş)</label>
                <select 
                  value={filters.period} 
                  onChange={(e) => handleFilterChange('period', e.target.value)}
                >
                  <option value="">Tüm Dönemler</option>
                  {availablePeriods?.map(period => (
                    <option key={period} value={period}>
                      {period}
                    </option>
                  ))}
                </select>
              </div>

              <div className="filter-actions">
                <button className="btn btn-primary" onClick={() => refetchDetailed()}>
                  <FaSearch /> Filtrele
                </button>
                <button className="btn btn-secondary" onClick={clearFilters}>
                  Temizle
                </button>
              </div>
            </div>
          </div>

          {/* Detaylı Kullanıcı Analizi */}
          {detailedAnalysis && (
            <>
              {/* Özet Kartları */}
              <div className="stats-section">
                <h2>Toplam İstatistikler</h2>
                <div className="summary-grid">
                  <div className="summary-card">
                    <h4>Toplam Oluşturulan</h4>
                    <p className="big-number">{detailedAnalysis.totals.statistics.total_created}</p>
                  </div>
                  <div className="summary-card">
                    <h4>Gönderilen</h4>
                    <p className="big-number">{detailedAnalysis.totals.statistics.total_sent}</p>
                  </div>
                  <div className="summary-card success">
                    <h4>Onaylanan</h4>
                    <p className="big-number">{detailedAnalysis.totals.statistics.total_approved}</p>
                  </div>
                  <div className="summary-card danger">
                    <h4>Reddedilen</h4>
                    <p className="big-number">{detailedAnalysis.totals.statistics.total_rejected}</p>
                  </div>
                  <div className="summary-card warning">
                    <h4>Bekleyen</h4>
                    <p className="big-number">{detailedAnalysis.totals.statistics.total_pending}</p>
                  </div>
                  <div className="summary-card">
                    <h4>Taslak</h4>
                    <p className="big-number">{detailedAnalysis.totals.statistics.total_draft}</p>
                  </div>
                </div>
              </div>

              {/* Kullanıcı Bazlı Detay Tablosu */}
              <div className="stats-section">
                <h2>Kullanıcı Bazlı Detay</h2>
                <div className="table-container">
                  <table className="detailed-table">
                    <thead>
                      <tr>
                        <th rowSpan="2">Kullanıcı</th>
                        <th rowSpan="2">Rol</th>
                        <th colSpan="7">Mutabakat İstatistikleri</th>
                        <th colSpan="3">Finansal Toplam (Onaylanan)</th>
                        <th rowSpan="2">Ort. Yanıt<br/>(Gün)</th>
                      </tr>
                      <tr>
                        <th>Oluşturulan</th>
                        <th>Gönderilen</th>
                        <th>Cevaplanmış</th>
                        <th>Onaylanan</th>
                        <th>Reddedilen</th>
                        <th>Bekleyen</th>
                        <th>Taslak</th>
                        <th>Borç</th>
                        <th>Alacak</th>
                        <th>Bakiye</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detailedAnalysis.users.map(user => (
                        <tr key={user.user_id}>
                          <td>
                            <div className="user-info">
                              <strong>{user.company_name || user.full_name}</strong>
                              <small>{user.username}</small>
                            </div>
                          </td>
                          <td>
                            <span className="role-badge">{getRoleText(user.role)}</span>
                          </td>
                          <td><strong>{user.statistics.total_created}</strong></td>
                          <td>{user.statistics.total_sent}</td>
                          <td>{user.statistics.total_answered}</td>
                          <td>
                            <span className="badge badge-success">
                              {user.statistics.total_approved}
                            </span>
                          </td>
                          <td>
                            <span className="badge badge-danger">
                              {user.statistics.total_rejected}
                            </span>
                          </td>
                          <td>
                            <span className="badge badge-warning">
                              {user.statistics.total_pending}
                            </span>
                          </td>
                          <td>
                            <span className="badge badge-secondary">
                              {user.statistics.total_draft}
                            </span>
                          </td>
                          <td className="amount">{formatCurrency(user.financial.total_borc)}</td>
                          <td className="amount">{formatCurrency(user.financial.total_alacak)}</td>
                          <td className="amount">{formatCurrency(user.financial.total_bakiye)}</td>
                          <td className="text-center">{user.statistics.avg_response_days}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="total-row">
                        <td colSpan="2"><strong>TOPLAM</strong></td>
                        <td><strong>{detailedAnalysis.totals.statistics.total_created}</strong></td>
                        <td><strong>{detailedAnalysis.totals.statistics.total_sent}</strong></td>
                        <td><strong>{detailedAnalysis.totals.statistics.total_answered}</strong></td>
                        <td><strong>{detailedAnalysis.totals.statistics.total_approved}</strong></td>
                        <td><strong>{detailedAnalysis.totals.statistics.total_rejected}</strong></td>
                        <td><strong>{detailedAnalysis.totals.statistics.total_pending}</strong></td>
                        <td><strong>{detailedAnalysis.totals.statistics.total_draft}</strong></td>
                        <td className="amount"><strong>{formatCurrency(detailedAnalysis.totals.financial.total_borc)}</strong></td>
                        <td className="amount"><strong>{formatCurrency(detailedAnalysis.totals.financial.total_alacak)}</strong></td>
                        <td className="amount"><strong>{formatCurrency(detailedAnalysis.totals.financial.total_bakiye)}</strong></td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Dönemsel Karşılaştırma Sekmesi */}
      {activeTab === 'period' && periodComparison && (
        <div className="tab-content">
          <div className="stats-section">
            <div className="heatmap-header">
              <h2>Son 12 Aylık Performans</h2>
              <div className="heatmap-controls">
                <label>Bitiş Dönemi:</label>
                <select 
                  value={comparisonPeriod} 
                  onChange={(e) => setComparisonPeriod(e.target.value)}
                  className="heatmap-select"
                >
                  <option value="">Bugüne Göre</option>
                  {availablePeriods?.map(period => (
                    <option key={period} value={period}>{period}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="period-chart">
              {periodComparison.map((period, index) => (
                <div key={index} className="period-item">
                  <div className="period-header">
                    <strong>{period.month}/{period.year}</strong>
                    <span className="period-total">{period.total} adet</span>
                  </div>
                  <div className="period-bars">
                    <div className="bar-row">
                      <span className="bar-label">Onaylanan</span>
                      <div className="bar-container">
                        <div 
                          className="bar success" 
                          style={{width: `${(period.approved / Math.max(period.total, 1)) * 100}%`}}
                        >
                          {period.approved > 0 && <span className="bar-value">{period.approved}</span>}
                        </div>
                      </div>
                    </div>
                    <div className="bar-row">
                      <span className="bar-label">Reddedilen</span>
                      <div className="bar-container">
                        <div 
                          className="bar danger" 
                          style={{width: `${(period.rejected / Math.max(period.total, 1)) * 100}%`}}
                        >
                          {period.rejected > 0 && <span className="bar-value">{period.rejected}</span>}
                        </div>
                      </div>
                    </div>
                    <div className="bar-row">
                      <span className="bar-label">Bekleyen</span>
                      <div className="bar-container">
                        <div 
                          className="bar warning" 
                          style={{width: `${(period.pending / Math.max(period.total, 1)) * 100}%`}}
                        >
                          {period.pending > 0 && <span className="bar-value">{period.pending}</span>}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="period-footer">
                    <small>Onay Oranı: <strong>{period.approval_rate}%</strong></small>
                    <small>Borç: {formatCurrency(period.total_borc)}</small>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Bekleyen Mutabakat Isı Haritası Sekmesi */}
      {activeTab === 'heatmap' && (
        <div className="tab-content">
          {heatmapData && (
            <>
              {/* Özet Bilgiler */}
              <div className="stats-section">
                <div className="heatmap-header">
                  <h2>Bekleyen Mutabakat Isı Haritası</h2>
                  <div className="heatmap-controls">
                    <label>Son kaç gün:</label>
                    <select 
                      value={heatmapDays} 
                      onChange={(e) => setHeatmapDays(Number(e.target.value))}
                      className="heatmap-select"
                    >
                      <option value={7}>7 Gün</option>
                      <option value={14}>14 Gün</option>
                      <option value={30}>30 Gün</option>
                      <option value={60}>60 Gün</option>
                      <option value={90}>90 Gün</option>
                    </select>
                  </div>
                </div>

                <div className="heatmap-summary">
                  <div className="summary-card">
                    <h4>Toplam Bekleyen</h4>
                    <p className="big-number">{heatmapData.total_pending}</p>
                  </div>
                  <div className="summary-card">
                    <h4>Ortalama Bekleme Süresi</h4>
                    <p className="big-number">{heatmapData.summary.avg_waiting_days} gün</p>
                  </div>
                  <div className="summary-card warning">
                    <h4>En Uzun Bekleme</h4>
                    <p className="big-number">{heatmapData.summary.max_waiting_days} gün</p>
                  </div>
                </div>
              </div>

              {/* Bekleme Süresine Göre Gruplandırma */}
              <div className="stats-section">
                <h2>Bekleme Süresine Göre Dağılım</h2>
                <div className="waiting-buckets">
                  {Object.entries(heatmapData.waiting_buckets).map(([bucket, count]) => {
                    const colors = {
                      "0-1": "#10b981",
                      "1-3": "#fbbf24",
                      "3-7": "#f97316",
                      "7-14": "#ef4444",
                      "14+": "#dc2626"
                    }
                    return (
                      <div key={bucket} className="bucket-card" style={{borderLeftColor: colors[bucket]}}>
                        <div className="bucket-header">
                          <h3>{bucket} gün</h3>
                          <span className="bucket-count">{count} adet</span>
                        </div>
                        <div className="bucket-bar">
                          <div 
                            className="bucket-fill" 
                            style={{
                              width: `${(count / heatmapData.total_pending) * 100}%`,
                              backgroundColor: colors[bucket]
                            }}
                          ></div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Günlük Dağılım Isı Haritası */}
              <div className="stats-section">
                <h2>Günlük Dağılım (Gönderim Tarihine Göre)</h2>
                <div className="daily-heatmap">
                  {heatmapData.daily_distribution.map((day, index) => {
                    const colorMap = {
                      green: "#10b981",
                      yellow: "#fbbf24",
                      orange: "#f97316",
                      red: "#ef4444"
                    }
                    const opacity = 0.3 + (day.intensity * 0.15)
                    return (
                      <div 
                        key={index} 
                        className="heatmap-cell"
                        style={{
                          backgroundColor: colorMap[day.color],
                          opacity: opacity,
                          borderColor: colorMap[day.color]
                        }}
                        title={`${day.date}: ${day.count} adet, Ort. ${day.avg_waiting_days} gün bekleme`}
                      >
                        <div className="cell-date">{new Date(day.date).toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' })}</div>
                        <div className="cell-count">{day.count}</div>
                        <div className="cell-days">{day.avg_waiting_days}g</div>
                      </div>
                    )
                  })}
                </div>
                <div className="heatmap-legend">
                  <div className="legend-item">
                    <span className="legend-color" style={{backgroundColor: "#10b981"}}></span>
                    <span>0-1 gün</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color" style={{backgroundColor: "#fbbf24"}}></span>
                    <span>1-3 gün</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color" style={{backgroundColor: "#f97316"}}></span>
                    <span>3-7 gün</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color" style={{backgroundColor: "#ef4444"}}></span>
                    <span>7+ gün</span>
                  </div>
                </div>
              </div>

              {/* Müşteri Bazlı Bekleme Süreleri */}
              <div className="stats-section">
                <h2>Müşteri Bazlı Bekleme Süreleri</h2>
                <div className="table-container">
                  <table className="detailed-table">
                    <thead>
                      <tr>
                        <th>Müşteri</th>
                        <th>Bekleyen Adet</th>
                        <th>Ort. Bekleme (Gün)</th>
                        <th>Max Bekleme (Gün)</th>
                        <th>Durum</th>
                      </tr>
                    </thead>
                    <tbody>
                      {heatmapData.customer_waiting.map((customer, index) => {
                        const colorMap = {
                          green: "#10b981",
                          yellow: "#fbbf24",
                          orange: "#f97316",
                          red: "#ef4444"
                        }
                        return (
                          <tr key={index}>
                            <td><strong>{customer.customer_name}</strong></td>
                            <td>{customer.pending_count}</td>
                            <td>{customer.avg_waiting_days}</td>
                            <td>{customer.max_waiting_days}</td>
                            <td>
                              <span 
                                className="status-badge" 
                                style={{backgroundColor: colorMap[customer.color]}}
                              >
                                {customer.color === 'green' ? 'İyi' : 
                                 customer.color === 'yellow' ? 'Orta' : 
                                 customer.color === 'orange' ? 'Dikkat' : 'Kritik'}
                              </span>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* En Uzun Bekleyenler */}
              <div className="stats-section">
                <h2>En Uzun Bekleyen Mutabakatlar (Top 10)</h2>
                <div className="table-container">
                  <table className="detailed-table">
                    <thead>
                      <tr>
                        <th>Mutabakat No</th>
                        <th>Müşteri</th>
                        <th>Bekleme Süresi</th>
                        <th>Gönderim Tarihi</th>
                        <th>Tutar</th>
                      </tr>
                    </thead>
                    <tbody>
                      {heatmapData.longest_waiting.map((item, index) => (
                        <tr key={index} className={item.waiting_days > 14 ? 'critical-row' : ''}>
                          <td><strong>{item.mutabakat_no}</strong></td>
                          <td>{item.receiver_name}</td>
                          <td>
                            <span className={`waiting-badge ${item.waiting_days > 14 ? 'critical' : item.waiting_days > 7 ? 'warning' : ''}`}>
                              {item.waiting_days} gün
                            </span>
                          </td>
                          <td>{item.send_date ? new Date(item.send_date).toLocaleDateString('tr-TR') : '-'}</td>
                          <td className="amount">{formatCurrency(item.amount)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Trend Grafikleri Sekmesi */}
      {activeTab === 'trends' && (
        <div className="tab-content">
          {timeSeriesData && (
            <>
              {/* Kontroller */}
              <div className="stats-section">
                <div className="heatmap-header">
                  <h2>Onay/Red Trend Analizi</h2>
                  <div className="heatmap-controls">
                    <label>Son kaç gün:</label>
                    <select 
                      value={trendDays} 
                      onChange={(e) => setTrendDays(Number(e.target.value))}
                      className="heatmap-select"
                    >
                      <option value={30}>30 Gün</option>
                      <option value={60}>60 Gün</option>
                      <option value={90}>90 Gün</option>
                      <option value={180}>180 Gün</option>
                      <option value={365}>365 Gün</option>
                    </select>
                    <label style={{marginLeft: '16px'}}>Gruplama:</label>
                    <select 
                      value={trendGroupBy} 
                      onChange={(e) => setTrendGroupBy(e.target.value)}
                      className="heatmap-select"
                    >
                      <option value="day">Günlük</option>
                      <option value="week">Haftalık</option>
                    </select>
                    <button 
                      className="btn btn-primary" 
                      onClick={handleExportCSV}
                      style={{marginLeft: '16px'}}
                    >
                      <FaDownload /> CSV İndir
                    </button>
                  </div>
                </div>
              </div>

              {/* Grafikler */}
              <div className="stats-section">
                <h3>Gönderilen, Onaylanan ve Reddedilen Mutabakatlar</h3>
                <div className="trend-chart-container">
                  {timeSeriesData.series && timeSeriesData.series.length > 0 ? (
                    <>
                      <div className="trend-chart">
                        {timeSeriesData.series.map((item, index) => {
                          const maxVal = Math.max(
                            ...timeSeriesData.series.map(s => Math.max(s.sent || 0, s.approved || 0, s.rejected || 0)),
                            1
                          )
                          const sentHeight = maxVal > 0 ? Math.max((item.sent || 0) / maxVal * 100, item.sent > 0 ? 5 : 0) : 0
                          const approvedHeight = maxVal > 0 ? Math.max((item.approved || 0) / maxVal * 100, item.approved > 0 ? 5 : 0) : 0
                          const rejectedHeight = maxVal > 0 ? Math.max((item.rejected || 0) / maxVal * 100, item.rejected > 0 ? 5 : 0) : 0
                          const label = trendGroupBy === 'week' ? item.bucket : new Date(item.bucket).toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' })
                          
                          return (
                            <div key={index} className="trend-bar-group">
                              <div className="trend-bars">
                                <div 
                                  className="trend-bar sent" 
                                  style={{height: `${sentHeight}%`}}
                                  title={`Gönderilen: ${item.sent || 0}`}
                                ></div>
                                <div 
                                  className="trend-bar approved" 
                                  style={{height: `${approvedHeight}%`}}
                                  title={`Onaylanan: ${item.approved || 0}`}
                                ></div>
                                <div 
                                  className="trend-bar rejected" 
                                  style={{height: `${rejectedHeight}%`}}
                                  title={`Reddedilen: ${item.rejected || 0}`}
                                ></div>
                              </div>
                              <div className="trend-label">{label}</div>
                            </div>
                          )
                        })}
                      </div>
                      <div className="trend-legend">
                        <div className="legend-item">
                          <span className="legend-color sent"></span>
                          <span>Gönderilen</span>
                        </div>
                        <div className="legend-item">
                          <span className="legend-color approved"></span>
                          <span>Onaylanan</span>
                        </div>
                        <div className="legend-item">
                          <span className="legend-color rejected"></span>
                          <span>Reddedilen</span>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div style={{padding: '40px', textAlign: 'center', color: 'var(--text-secondary)'}}>
                      <p>Bu dönem için veri bulunamadı.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Ortalama Onay Süresi */}
              <div className="stats-section">
                <h3>Ortalama Onay Süresi (Gün)</h3>
                <div className="trend-chart-container">
                  {timeSeriesData.series && timeSeriesData.series.length > 0 ? (
                    <div className="trend-chart">
                      {timeSeriesData.series.map((item, index) => {
                        const responseDays = item.avg_response_days || 0
                        const maxDays = Math.max(
                          ...timeSeriesData.series.map(s => s.avg_response_days || 0),
                          1
                        )
                        const height = maxDays > 0 && responseDays > 0 
                          ? Math.max((responseDays / maxDays) * 100, 5) 
                          : 0
                        const label = trendGroupBy === 'week' ? item.bucket : new Date(item.bucket).toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' })
                        
                        return (
                          <div key={index} className="trend-bar-group">
                            <div className="trend-bars">
                              <div 
                                className="trend-bar response-time" 
                                style={{height: `${height}%`}}
                                title={`Ort. Onay Süresi: ${responseDays.toFixed(2)} gün`}
                              >
                                {responseDays > 0 && (
                                  <span className="bar-value">{responseDays.toFixed(1)}</span>
                                )}
                              </div>
                            </div>
                            <div className="trend-label">{label}</div>
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <div style={{padding: '40px', textAlign: 'center', color: 'var(--text-secondary)'}}>
                      <p>Bu dönem için ortalama onay süresi verisi bulunamadı.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Özet Tablo */}
              <div className="stats-section">
                <h3>Detaylı Veriler</h3>
                <div className="table-container">
                  <table className="detailed-table">
                    <thead>
                      <tr>
                        <th>{trendGroupBy === 'week' ? 'Hafta' : 'Tarih'}</th>
                        <th>Gönderilen</th>
                        <th>Onaylanan</th>
                        <th>Reddedilen</th>
                        <th>Ort. Onay Süresi (Gün)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {timeSeriesData.series.map((item, index) => (
                        <tr key={index}>
                          <td><strong>{trendGroupBy === 'week' ? item.bucket : new Date(item.bucket).toLocaleDateString('tr-TR')}</strong></td>
                          <td>{item.sent}</td>
                          <td><span className="badge badge-success">{item.approved}</span></td>
                          <td><span className="badge badge-danger">{item.rejected}</span></td>
                          <td>{item.avg_response_days > 0 ? item.avg_response_days.toFixed(2) : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Gün-Saat Isı Haritası Sekmesi */}
      {activeTab === 'dayhour' && (
        <div className="tab-content">
          {dayHourData && (
            <>
              {/* Kontroller */}
              <div className="stats-section">
                <div className="heatmap-header">
                  <h2>Gün-Saat Isı Haritası (Bekleyen Mutabakatlar)</h2>
                  <div className="heatmap-controls">
                    <label>Son kaç gün:</label>
                    <select 
                      value={dayHourDays} 
                      onChange={(e) => setDayHourDays(Number(e.target.value))}
                      className="heatmap-select"
                    >
                      <option value={7}>7 Gün</option>
                      <option value={14}>14 Gün</option>
                      <option value={30}>30 Gün</option>
                      <option value={60}>60 Gün</option>
                      <option value={90}>90 Gün</option>
                    </select>
                  </div>
                </div>
                <p style={{color: 'var(--text-secondary)', marginTop: '8px'}}>
                  Gönderilmiş ama henüz cevaplanmamış mutabakatların gün ve saat bazında dağılımı
                </p>
              </div>

              {/* 7x24 Isı Haritası */}
              <div className="stats-section">
                <h3>Gün-Saat Dağılımı</h3>
                <div className="day-hour-heatmap-container">
                  <div className="day-hour-heatmap">
                    {/* Saat başlıkları */}
                    <div className="day-hour-header">
                      <div className="day-hour-cell header"></div>
                      {Array.from({length: 24}, (_, h) => (
                        <div key={h} className="day-hour-cell header">{h}</div>
                      ))}
                      <div className="day-hour-cell header">Toplam</div>
                    </div>
                    
                    {/* Günler */}
                    {['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'].map((dayName, d) => {
                      const row = dayHourData.matrix[d]
                      const total = dayHourData.totals_by_day[d]
                      const maxVal = dayHourData.max || 1
                      
                      return (
                        <div key={d} className="day-hour-row">
                          <div className="day-hour-cell day-label">{dayName}</div>
                          {row.map((count, h) => {
                            const intensity = maxVal > 0 ? count / maxVal : 0
                            const opacity = 0.3 + (intensity * 0.7)
                            const color = intensity > 0.7 ? '#ef4444' : intensity > 0.4 ? '#f97316' : intensity > 0.2 ? '#fbbf24' : '#10b981'
                            
                            return (
                              <div 
                                key={h}
                                className="day-hour-cell heatmap-cell"
                                style={{
                                  backgroundColor: color,
                                  opacity: opacity,
                                  borderColor: color
                                }}
                                title={`${dayName} ${h}:00 - ${count} adet`}
                              >
                                {count > 0 && <span className="cell-count">{count}</span>}
                              </div>
                            )
                          })}
                          <div className="day-hour-cell total-cell">
                            <strong>{total}</strong>
                          </div>
                        </div>
                      )
                    })}
                    
                    {/* Saat toplamları */}
                    <div className="day-hour-row">
                      <div className="day-hour-cell header">Toplam</div>
                      {dayHourData.totals_by_hour.map((total, h) => (
                        <div key={h} className="day-hour-cell total-cell">
                          <strong>{total}</strong>
                        </div>
                      ))}
                      <div className="day-hour-cell total-cell">
                        <strong>{dayHourData.totals_by_day.reduce((a, b) => a + b, 0)}</strong>
                      </div>
                    </div>
                  </div>
                  
                  <div className="day-hour-legend">
                    <div className="legend-item">
                      <span className="legend-color" style={{backgroundColor: '#10b981'}}></span>
                      <span>Düşük (0-20%)</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-color" style={{backgroundColor: '#fbbf24'}}></span>
                      <span>Orta (20-40%)</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-color" style={{backgroundColor: '#f97316'}}></span>
                      <span>Yüksek (40-70%)</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-color" style={{backgroundColor: '#ef4444'}}></span>
                      <span>Çok Yüksek (70%+)</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
