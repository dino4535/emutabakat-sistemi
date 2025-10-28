import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { 
  FaChartLine, FaUsers, FaFileInvoice, FaCheckCircle, FaTimesCircle, 
  FaClock, FaTrophy, FaFilter, FaSearch, FaChartBar, FaTable 
} from 'react-icons/fa'
import './Reports.css'

export default function Reports() {
  const [activeTab, setActiveTab] = useState('overview') // overview, detailed, period
  const [filters, setFilters] = useState({
    userId: '',
    period: ''
  })

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

  // Dönemsel karşılaştırma
  const { data: periodComparison } = useQuery({
    queryKey: ['reports-period-comparison'],
    queryFn: async () => {
      const response = await axios.get('/api/reports/period-comparison')
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
      </div>

      {/* Genel Bakış Sekmesi */}
      {activeTab === 'overview' && (
        <div className="tab-content">
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
            <h2>Son 12 Aylık Performans</h2>
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
    </div>
  )
}
