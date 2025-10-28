import { useNavigate } from 'react-router-dom'
import { 
  FaPlus, 
  FaFileUpload, 
  FaUsers, 
  FaChartLine,
  FaFileAlt,
  FaCog 
} from 'react-icons/fa'
import './QuickActions.css'

/**
 * Quick Actions Component
 * Hızlı erişim butonları
 */
export default function QuickActions({ userRole }) {
  const navigate = useNavigate()

  const actions = [
    {
      icon: <FaPlus />,
      label: 'Yeni Mutabakat',
      color: '#3b82f6',
      onClick: () => navigate('/mutabakat/create'),
      roles: ['ADMIN', 'COMPANY_ADMIN', 'MUHASEBE', 'PLANLAMA']
    },
    {
      icon: <FaFileUpload />,
      label: 'Toplu Yükleme',
      color: '#8b5cf6',
      onClick: () => navigate('/bulk-mutabakat'),
      roles: ['ADMIN', 'COMPANY_ADMIN', 'MUHASEBE', 'PLANLAMA']
    },
    {
      icon: <FaUsers />,
      label: 'Kullanıcılar',
      color: '#10b981',
      onClick: () => navigate('/users'),
      roles: ['ADMIN', 'COMPANY_ADMIN']
    },
    {
      icon: <FaChartLine />,
      label: 'Raporlar',
      color: '#f59e0b',
      onClick: () => navigate('/reports'),
      roles: ['ADMIN', 'COMPANY_ADMIN', 'MUHASEBE']
    },
    {
      icon: <FaFileAlt />,
      label: 'Mutabakatlar',
      color: '#06b6d4',
      onClick: () => navigate('/mutabakat'),
      roles: ['ADMIN', 'COMPANY_ADMIN', 'MUHASEBE', 'PLANLAMA', 'MUSTERI', 'TEDARIKCI']
    },
    {
      icon: <FaCog />,
      label: 'Ayarlar',
      color: '#6b7280',
      onClick: () => navigate('/profile'),
      roles: ['ADMIN', 'COMPANY_ADMIN', 'MUHASEBE', 'PLANLAMA', 'MUSTERI', 'TEDARIKCI']
    }
  ]

  // Kullanıcı rolüne göre filtrele
  const visibleActions = actions.filter(action => 
    action.roles.includes(userRole)
  )

  return (
    <div className="quick-actions">
      <h3 className="quick-actions-title">⚡ Hızlı İşlemler</h3>
      <div className="quick-actions-grid">
        {visibleActions.map((action, index) => (
          <button
            key={index}
            className="quick-action-btn"
            onClick={action.onClick}
            style={{ '--action-color': action.color }}
          >
            <div className="quick-action-icon" style={{ backgroundColor: `${action.color}15`, color: action.color }}>
              {action.icon}
            </div>
            <span className="quick-action-label">{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

