import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { FaFileAlt, FaClock, FaCheckCircle, FaTimesCircle, FaMoneyBillWave } from 'react-icons/fa'
import { useAuth } from '../contexts/AuthContext'
import AnimatedCounter from '../components/AnimatedCounter'
import TrendIndicator from '../components/TrendIndicator'
import QuickActions from '../components/QuickActions'
import RecentActivities from '../components/RecentActivities'
import RecentAuditLogs from '../components/RecentAuditLogs'
import SkeletonLoader from '../components/SkeletonLoader'
import './Dashboard.css'

export default function Dashboard() {
  const { user } = useAuth()
  
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await axios.get('/api/dashboard/stats')
      return response.data
    },
    refetchInterval: 60000 // 1 dakikada bir yenile
  })

  if (isLoading) {
    return (
      <div className="dashboard animate-fadeIn">
        <div className="dashboard-header">
          <h1>Dashboard</h1>
          <p>Hoş geldiniz!</p>
        </div>
        <div className="stats-grid">
          <SkeletonLoader type="stats-card" count={4} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '24px' }}>
          <SkeletonLoader type="card" height="400px" />
          <SkeletonLoader type="card" height="400px" />
        </div>
      </div>
    )
  }

  const cards = [
    {
      title: 'Toplam Mutabakat',
      value: stats?.toplam_mutabakat || 0,
      icon: <FaFileAlt />,
      color: '#3b82f6',
      bgColor: '#dbeafe',
      trend: stats?.toplam_trend || 0
    },
    {
      title: 'Bekleyen',
      value: stats?.bekleyen_mutabakat || 0,
      icon: <FaClock />,
      color: '#f59e0b',
      bgColor: '#fed7aa',
      trend: stats?.bekleyen_trend || 0,
      isPositiveBetter: false // Bekleyen azalması iyi
    },
    {
      title: 'Onaylanan',
      value: stats?.onaylanan_mutabakat || 0,
      icon: <FaCheckCircle />,
      color: '#10b981',
      bgColor: '#d1fae5',
      trend: stats?.onaylanan_trend || 0
    },
    {
      title: 'Reddedilen',
      value: stats?.reddedilen_mutabakat || 0,
      icon: <FaTimesCircle />,
      color: '#ef4444',
      bgColor: '#fee2e2',
      trend: stats?.reddedilen_trend || 0,
      isPositiveBetter: false // Reddedilen azalması iyi
    }
  ]

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0)
  }

  const bakiye = (stats?.toplam_alacak || 0) - (stats?.toplam_borc || 0)

  return (
    <div className="dashboard animate-fadeInUp">
      {/* Header */}
      <div className="dashboard-header animate-fadeIn">
        <div>
          <h1>👋 Merhaba, {user?.full_name || user?.username}</h1>
          <p>Bugün {new Date().toLocaleDateString('tr-TR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
        <div className="header-actions">
          <button className="refresh-btn" onClick={() => window.location.reload()}>
            🔄 Yenile
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="stats-grid">
        {cards.map((card, index) => (
          <div 
            key={index} 
            className="stat-card modern-card" 
            style={{ 
              borderLeft: `4px solid ${card.color}`,
              animationDelay: `${index * 100}ms`
            }}
          >
            <div className="stat-icon" style={{ backgroundColor: card.bgColor, color: card.color }}>
              {card.icon}
            </div>
            <div className="stat-content">
              <p className="stat-title">{card.title}</p>
              <h2 className="stat-value">
                <AnimatedCounter value={card.value} duration={1500} />
              </h2>
              {card.trend !== undefined && card.trend !== 0 && (
                <TrendIndicator 
                  value={card.value} 
                  change={card.trend}
                  isPositiveBetter={card.isPositiveBetter !== false}
                />
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Financial Summary */}
      <div className="financial-summary">
        <div className="card modern-card">
          <h3>
            <FaMoneyBillWave /> Mali Özet
          </h3>
          <div className="financial-grid">
            <div className="financial-item">
              <span className="financial-label">Toplam Borç</span>
              <span className="financial-value borc">
                <AnimatedCounter 
                  value={stats?.toplam_borc || 0} 
                  decimals={0}
                  suffix=" ₺"
                  duration={2000}
                />
              </span>
            </div>
            <div className="financial-item">
              <span className="financial-label">Toplam Alacak</span>
              <span className="financial-value alacak">
                <AnimatedCounter 
                  value={stats?.toplam_alacak || 0} 
                  decimals={0}
                  suffix=" ₺"
                  duration={2000}
                />
              </span>
            </div>
            <div className="financial-item">
              <span className="financial-label">Net Bakiye</span>
              <span className={`financial-value ${bakiye >= 0 ? 'alacak' : 'borc'}`}>
                <AnimatedCounter 
                  value={bakiye} 
                  decimals={0}
                  suffix=" ₺"
                  duration={2000}
                />
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions & Recent Activities */}
      <div className="dashboard-bottom">
        <QuickActions userRole={user?.role} />
        <RecentActivities />
      </div>

      {/* Audit Logs (Sadece Admin) */}
      {['admin', 'company_admin'].includes(user?.role) && (
        <div className="dashboard-bottom" style={{ marginTop: '24px' }}>
          <RecentAuditLogs />
        </div>
      )}
    </div>
  )
}
