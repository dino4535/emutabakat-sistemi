import { useState, useRef, useEffect } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { formatDistanceToNow } from 'date-fns'
import { tr } from 'date-fns/locale'
import { FaHome, FaFileAlt, FaPlus, FaSignOutAlt, FaUser, FaUsers, FaCog, FaChartLine, FaBars, FaShieldAlt, FaUserCog, FaBell, FaSearch, FaCheckCircle, FaExclamationCircle, FaInfoCircle, FaStore, FaGavel, FaBuilding, FaHistory } from 'react-icons/fa'
import { Notification } from './Notification'
import { useSwipe } from '../hooks/useSwipe'
import './Layout.css'

export default function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [showNotifications, setShowNotifications] = useState(false)
  const notificationRef = useRef(null)

  // Touch gesture desteği - mobilde menüyü açıp kapatmak için
  const swipeRef = useSwipe(
    () => setIsSidebarOpen(false), // Sola kaydır -> Menü kapat
    () => setIsSidebarOpen(true)    // Sağa kaydır -> Menü aç
  )

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen)
  }

  // Body'ye durum sınıfı ekle (mobilde overlay varken üst öğeler tıklanmasın)
  useEffect(() => {
    if (isSidebarOpen) {
      document.body.classList.add('sidebar-open')
    } else {
      document.body.classList.remove('sidebar-open')
    }
    return () => document.body.classList.remove('sidebar-open')
  }, [isSidebarOpen])

  const isActive = (path) => location.pathname === path
  
  // Rollere göre menü kontrolü
  const canCreateMutabakat = ['admin', 'company_admin', 'muhasebe', 'planlama'].includes(user?.role)
  const isAdmin = ['admin', 'company_admin'].includes(user?.role)  // Sistem admini veya şirket admini
  const isSystemAdmin = user?.role === 'admin'  // Sadece sistem admini

  // Bildirim dropdown'unu dışarıya tıklayınca kapat
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setShowNotifications(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Gerçek bildirimleri API'den çek
  const { data: notificationsData, isLoading: notificationsLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => {
      const response = await axios.get('/api/notifications/')
      return response.data
    },
    refetchInterval: 60000, // Her 60 saniyede bir güncelle
    enabled: !!user // Kullanıcı varsa çalıştır
  })

  const notifications = notificationsData || []

  // Bildirimi oku ve sayfaya git
  const handleNotificationClick = (notification) => {
    // Dropdown'u kapat
    setShowNotifications(false)
    
    // Sayfaya yönlendir
    if (notification.link) {
      navigate(notification.link)
    }
  }

  // Toplam bildirim sayısı (hepsi okunmamış sayılır)
  const unreadCount = notifications.length

  const getNotificationIcon = (type) => {
    switch(type) {
      case 'pending_approval': return <FaExclamationCircle style={{ color: '#ed8936' }} />
      case 'waiting_approval': return <FaExclamationCircle style={{ color: '#f56565' }} />
      case 'approved': return <FaCheckCircle style={{ color: '#48bb78' }} />
      case 'rejected': return <FaExclamationCircle style={{ color: '#f56565' }} />
      case 'draft': return <FaInfoCircle style={{ color: '#4299e1' }} />
      default: return <FaBell />
    }
  }

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <div className="header-left">
            <button 
              className="menu-toggle-btn" 
              onClick={toggleSidebar}
              title={isSidebarOpen ? "Menüyü Kapat" : "Menüyü Aç"}
            >
              <FaBars />
            </button>
            <img 
              src={user?.company_logo ? `/${user.company_logo}` : "/dino-logo.png"} 
              alt={user?.company_name || "Şirket"} 
              className="company-logo" 
            />
            <h1 className="app-title">E-Mutabakat</h1>
          </div>
          <div className="header-right">
            <div className="welcome-message">
              <span className="welcome-text">Hoş geldiniz!</span>
              <span className="user-company">{user?.company_name || user?.full_name}</span>
            </div>
            
            {/* Bildirimler Dropdown */}
            <div className="notification-wrapper" ref={notificationRef}>
              <button 
                className="header-icon-btn" 
                title="Bildirimler"
                onClick={() => setShowNotifications(!showNotifications)}
              >
                <FaBell />
                {unreadCount > 0 && (
                  <span className="notification-badge">{unreadCount}</span>
                )}
              </button>
              
              {showNotifications && (
                <div className="notification-dropdown">
                  <div className="notification-header">
                    <h4>Bildirimler</h4>
                    <span className="notification-count">{unreadCount} bildirim</span>
                  </div>
                  <div className="notification-list">
                    {notificationsLoading ? (
                      <div className="notification-empty">
                        <p>Yükleniyor...</p>
                      </div>
                    ) : notifications.length > 0 ? (
                      notifications.map(notif => {
                        // Relative time hesapla
                        const relativeTime = formatDistanceToNow(new Date(notif.date), { 
                          addSuffix: true, 
                          locale: tr 
                        })
                        
                        return (
                          <div 
                            key={notif.id} 
                            className={`notification-item unread priority-${notif.priority || 'medium'}`}
                            onClick={() => handleNotificationClick(notif)}
                          >
                            <div className="notification-icon">
                              {getNotificationIcon(notif.type)}
                            </div>
                            <div className="notification-content">
                              <div className="notification-title">{notif.title}</div>
                              <div className="notification-message">{notif.message}</div>
                              <div className="notification-time">{relativeTime}</div>
                            </div>
                            <div className="unread-dot"></div>
                          </div>
                        )
                      })
                    ) : (
                      <div className="notification-empty">
                        <FaBell style={{ fontSize: '32px', opacity: 0.3 }} />
                        <p>Bildiriminiz yok</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Kullanıcı Menüsü */}
            <div className="user-menu">
              <Link to="/profile" className="user-avatar" title="Profil">
                {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
              </Link>
              <button onClick={handleLogout} className="logout-btn" title="Çıkış">
                <FaSignOutAlt />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="main-container">
        {/* Mobil için backdrop */}
        {isSidebarOpen && (
          <div className="sidebar-backdrop" onClick={toggleSidebar}></div>
        )}
        
        <aside className={`sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
          <nav
            className="nav"
            onClick={(e) => {
              const el = e.target.closest('a,button')
              if (el) {
                // Navigasyonun gerçekleşmesini engellemeden menüyü kapat
                setTimeout(() => setIsSidebarOpen(false), 0)
              }
            }}
          >
            {/* Ana Menü */}
            <div className="nav-section">
              <div className="nav-section-title">Menü</div>
              <Link
                to="/dashboard"
                className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
              >
                <FaHome />
                <span>Dashboard</span>
              </Link>
            </div>

            {/* Mutabakat İşlemleri */}
            <div className="nav-section">
              <div className="nav-section-title">Mutabakat İşlemleri</div>
              <Link
                to="/mutabakat"
                className={`nav-link ${isActive('/mutabakat') ? 'active' : ''}`}
              >
                <FaFileAlt />
                <span>Mutabakatlar</span>
              </Link>
              {canCreateMutabakat && (
                <>
                  <Link
                    to="/mutabakat/new"
                    className={`nav-link ${isActive('/mutabakat/new') ? 'active' : ''}`}
                  >
                    <FaPlus />
                    <span>Manuel Mutabakat</span>
                  </Link>
                  <Link
                    to="/mutabakat/bulk"
                    className={`nav-link ${isActive('/mutabakat/bulk') ? 'active' : ''}`}
                  >
                    <FaUsers />
                    <span>Toplu Mutabakat</span>
                  </Link>
                  <Link
                    to="/bayi/bulk"
                    className={`nav-link ${isActive('/bayi/bulk') ? 'active' : ''}`}
                  >
                    <FaStore />
                    <span>Toplu Bayi Yükleme</span>
                  </Link>
                </>
              )}
            </div>
            
            {/* Yönetim (Sadece Admin) */}
            {isAdmin && (
              <div className="nav-section">
                <div className="nav-section-title">Yönetim</div>
                <Link
                  to="/reports"
                  className={`nav-link ${isActive('/reports') ? 'active' : ''}`}
                >
                  <FaChartLine />
                  <span>Raporlar</span>
                </Link>
                <Link
                  to="/legal-reports"
                  className={`nav-link ${isActive('/legal-reports') ? 'active' : ''}`}
                >
                  <FaGavel />
                  <span>Yasal Raporlar</span>
                </Link>
                <Link
                  to="/verify"
                  className={`nav-link ${isActive('/verify') ? 'active' : ''}`}
                >
                  <FaShieldAlt />
                  <span>Dijital İmza</span>
                </Link>
                <Link
                  to="/users"
                  className={`nav-link ${isActive('/users') ? 'active' : ''}`}
                >
                  <FaUserCog />
                  <span>Kullanıcılar</span>
                </Link>
                <Link
                  to="/audit-logs"
                  className={`nav-link ${isActive('/audit-logs') ? 'active' : ''}`}
                >
                  <FaHistory />
                  <span>Audit Logs</span>
                </Link>
              </div>
            )}
            
            {/* Sistem Yönetimi (Sadece Sistem Admini) */}
            {isSystemAdmin && (
              <div className="nav-section">
                <div className="nav-section-title">Sistem</div>
                <Link
                  to="/companies"
                  className={`nav-link ${isActive('/companies') ? 'active' : ''}`}
                >
                  <FaBuilding />
                  <span>Şirket Yönetimi</span>
                </Link>
              </div>
            )}

            {/* Diğer */}
            <div className="nav-section">
              <div className="nav-section-title">Diğer</div>
              <Link
                to="/profile"
                className={`nav-link ${isActive('/profile') ? 'active' : ''}`}
              >
                <FaCog />
                <span>Profil Ayarları</span>
              </Link>
              {/* Push bildirim butonu kaldırıldı */}
            </div>

            {/* Mobil için hızlı işlemler */}
            <div className="nav-section mobile-only">
              <div className="nav-section-title">Hızlı İşlemler</div>
              <Link to="/profile" className="nav-link">
                <FaUser />
                <span>Profil</span>
              </Link>
              <button onClick={handleLogout} className="nav-link" style={{ background: 'transparent', border: 0 }}>
                <FaSignOutAlt />
                <span>Çıkış</span>
              </button>
            </div>
          </nav>
        </aside>

        <main ref={swipeRef} className={`content ${isSidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
          <Outlet />
        </main>
      </div>
      
      {/* Global Notification System */}
      <Notification />
    </div>
  )
}

