import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'react-toastify'
import { FaUser, FaEnvelope, FaPhone, FaBuilding, FaIdCard, FaMapMarkerAlt, FaLock, FaSave, FaExclamationTriangle, FaShieldAlt, FaCheckCircle, FaClock, FaStore } from 'react-icons/fa'
import LoadingButton from '../components/LoadingButton'
import SkeletonLoader from '../components/SkeletonLoader'
import './Profile.css'
import '../styles/kvkk-profile.css'

export default function Profile() {
  const { user, updateUser } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  // İlk giriş kontrolü
  const isFirstLogin = user?.ilk_giris_tamamlandi === false
  
  const [activeTab, setActiveTab] = useState('profile')
  
  // KVKK onay durumunu çek
  const { data: kvkkConsent } = useQuery({
    queryKey: ['kvkk-consent'],
    queryFn: async () => {
      try {
        const response = await axios.get('/api/kvkk/consent/status')
        return response.data
      } catch (error) {
        // Onay kaydı yoksa null döndür
        if (error.response?.status === 404) {
          return null
        }
        throw error
      }
    }
  })
  
  // Bayileri çek (sadece müşteri ve tedarikçi için)
  const { data: bayilerData, isLoading: bayilerLoading } = useQuery({
    queryKey: ['user-bayiler', user?.vkn_tckn],
    queryFn: async () => {
      if (!user?.vkn_tckn) return null
      try {
        const response = await axios.get(`/api/bayi/by-vkn/${user.vkn_tckn}`)
        return response.data
      } catch (error) {
        if (error.response?.status === 404) {
          return null // Bayi kaydı yok
        }
        throw error
      }
    },
    enabled: !!user?.vkn_tckn && ['musteri', 'tedarikci'].includes(user?.role)
  })
  const [profileData, setProfileData] = useState({
    email: user?.email || '',
    full_name: user?.full_name || '',
    company_name: user?.company_name || '',
    vkn_tckn: user?.vkn_tckn || '',
    tax_office: user?.tax_office || '',
    phone: user?.phone || '',
    address: user?.address || ''
  })
  
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })

  // Profil güncelleme mutation
  const updateProfileMutation = useMutation({
    mutationFn: async (data) => {
      const response = await axios.put('/api/auth/profile', data)
      return response.data
    },
    onSuccess: (data) => {
      toast.success('Profil bilgileriniz başarıyla güncellendi!')
      queryClient.invalidateQueries(['current-user'])
      
      // İlk girişse kullanıcıyı güncelle ve dashboard'a yönlendir
      if (isFirstLogin) {
        updateUser(data)
        toast.success('Hoş geldiniz! Profil bilgileriniz tamamlandı.')
        setTimeout(() => {
          navigate('/dashboard')
        }, 1000)
      }
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Profil güncellenemedi')
    }
  })

  // Şifre değiştirme mutation
  const changePasswordMutation = useMutation({
    mutationFn: async (data) => {
      const response = await axios.post('/api/auth/change-password', {
        current_password: data.current_password,
        new_password: data.new_password
      })
      return response.data
    },
    onSuccess: () => {
      toast.success('Şifreniz başarıyla değiştirildi!')
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Şifre değiştirilemedi')
    }
  })

  const handleProfileSubmit = (e) => {
    e.preventDefault()
    
    // İlk giriş kontrolü - Email ve telefon zorunlu
    if (isFirstLogin) {
      if (!profileData.email || !profileData.email.includes('@')) {
        toast.error('Lütfen geçerli bir e-posta adresi girin')
        return
      }
      if (!profileData.phone || profileData.phone.length < 10) {
        toast.error('Lütfen geçerli bir telefon numarası girin')
        return
      }
    }
    
    // Boş alanları çıkar
    const updates = {}
    Object.keys(profileData).forEach(key => {
      if (profileData[key] && profileData[key] !== user?.[key]) {
        updates[key] = profileData[key]
      }
    })
    
    // İlk giriş ise flag'i güncelle
    if (isFirstLogin) {
      updates.ilk_giris_tamamlandi = true
    }
    
    if (Object.keys(updates).length === 0 && !isFirstLogin) {
      toast.info('Değişiklik yapılmadı')
      return
    }
    
    updateProfileMutation.mutate(updates)
  }

  const handlePasswordSubmit = (e) => {
    e.preventDefault()
    
    if (!passwordData.current_password || !passwordData.new_password) {
      toast.error('Lütfen tüm alanları doldurun')
      return
    }
    
    if (passwordData.new_password.length < 6) {
      toast.error('Yeni şifre en az 6 karakter olmalıdır')
      return
    }
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('Yeni şifreler eşleşmiyor')
      return
    }
    
    changePasswordMutation.mutate(passwordData)
  }

  const getRoleName = (role) => {
    const roles = {
      admin: 'Sistem Yöneticisi',
      muhasebe: 'Muhasebe',
      planlama: 'Planlama',
      musteri: 'Müşteri',
      tedarikci: 'Tedarikçi'
    }
    return roles[role] || role
  }

  return (
    <div className="profile-page">
      <div className="profile-header">
        <div className="profile-header-left">
          <h1>👤 Profil Ayarları</h1>
          <p>Hesap bilgilerinizi görüntüleyin ve güncelleyin</p>
        </div>
      </div>

      {/* İlk Giriş Uyarısı */}
      {isFirstLogin && (
        <div className="first-login-banner" style={{
          backgroundColor: '#fff3cd',
          border: '1px solid #ffc107',
          borderRadius: '8px',
          padding: '16px 20px',
          margin: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <FaExclamationTriangle style={{ color: '#ff9800', fontSize: '24px' }} />
          <div>
            <h3 style={{ margin: '0 0 4px 0', color: '#856404', fontSize: '16px', fontWeight: '600' }}>
              Profil Bilgilerinizi Tamamlayın
            </h3>
            <p style={{ margin: 0, color: '#856404', fontSize: '14px' }}>
              Lütfen <strong>e-posta adresinizi</strong> ve <strong>telefon numaranızı</strong> girerek profil bilgilerinizi tamamlayın. 
              Bu bilgiler mutabakat süreçleriniz için gereklidir.
            </p>
          </div>
        </div>
      )}

      <div className="profile-content">
        {/* Sol Taraf - Kullanıcı Kartı */}
        <div className="profile-sidebar">
          <div className="profile-card">
            <div className="profile-avatar">
              <FaUser />
            </div>
            <h2>{user?.full_name || user?.username}</h2>
            <p className="profile-role">{getRoleName(user?.role)}</p>
            <p className="profile-email">{user?.email}</p>
            
            <div className="profile-info-grid">
              <div className="profile-info-item">
                <span className="info-label">Kullanıcı Adı</span>
                <span className="info-value">{user?.username}</span>
              </div>
              {user?.tax_office && (
                <div className="profile-info-item">
                  <span className="info-label">Vergi Dairesi</span>
                  <span className="info-value">{user.tax_office}</span>
                </div>
              )}
              <div className="profile-info-item">
                <span className="info-label">Üyelik Tarihi</span>
                <span className="info-value">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString('tr-TR') : '-'}
                </span>
              </div>
              <div className="profile-info-item">
                <span className="info-label">Durum</span>
                <span className={`status-badge ${user?.is_active ? 'active' : 'inactive'}`}>
                  {user?.is_active ? 'Aktif' : 'Pasif'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Sağ Taraf - Form Alanı */}
        <div className="profile-main">
          <div className="profile-tabs">
            <button
              className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
              onClick={() => setActiveTab('profile')}
            >
              <FaUser /> Profil Bilgileri
            </button>
            <button
              className={`tab-button ${activeTab === 'password' ? 'active' : ''} ${isFirstLogin ? 'disabled' : ''}`}
              onClick={() => !isFirstLogin && setActiveTab('password')}
              disabled={isFirstLogin}
              title={isFirstLogin ? 'Önce profil bilgilerinizi tamamlayın' : ''}
            >
              <FaLock /> Şifre Değiştir
            </button>
            <button
              className={`tab-button ${activeTab === 'kvkk' ? 'active' : ''} ${isFirstLogin ? 'disabled' : ''}`}
              onClick={() => !isFirstLogin && setActiveTab('kvkk')}
              disabled={isFirstLogin}
              title={isFirstLogin ? 'Önce profil bilgilerinizi tamamlayın' : ''}
            >
              <FaShieldAlt /> KVKK Onaylarım
              {kvkkConsent && (
                <span className="badge-sm badge-success" style={{ marginLeft: '8px' }}>✓</span>
              )}
            </button>
            {['musteri', 'tedarikci'].includes(user?.role) && (
              <button
                className={`tab-button ${activeTab === 'bayiler' ? 'active' : ''} ${isFirstLogin ? 'disabled' : ''}`}
                onClick={() => !isFirstLogin && setActiveTab('bayiler')}
                disabled={isFirstLogin}
                title={isFirstLogin ? 'Önce profil bilgilerinizi tamamlayın' : ''}
              >
                <FaStore /> Bayilerim
                {bayilerData?.toplam_bayi_sayisi > 0 && (
                  <span className="badge-sm badge-info" style={{ marginLeft: '8px' }}>
                    {bayilerData.toplam_bayi_sayisi}
                  </span>
                )}
              </button>
            )}
          </div>

          {activeTab === 'profile' && (
            <form onSubmit={handleProfileSubmit} className="profile-form">
              <div className="form-section">
                <h3>Kişisel Bilgiler</h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label">
                      <FaUser /> Ad Soyad *
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      value={profileData.full_name}
                      onChange={(e) => setProfileData({...profileData, full_name: e.target.value})}
                      placeholder="Adınız ve soyadınız"
                      required
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="form-label">
                      <FaEnvelope /> E-posta Adresi *
                    </label>
                    <input
                      type="email"
                      className="form-input"
                      value={profileData.email}
                      onChange={(e) => setProfileData({...profileData, email: e.target.value})}
                      placeholder="ornek@email.com"
                      required
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="form-label">
                      <FaPhone /> Telefon Numarası {isFirstLogin && '*'}
                    </label>
                    <input
                      type="tel"
                      className="form-input"
                      value={profileData.phone}
                      onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                      placeholder="+90 (5XX) XXX XX XX"
                      required={isFirstLogin}
                    />
                  </div>
                </div>
              </div>

              <div className="form-section">
                <h3>Firma Bilgileri</h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label">
                      <FaBuilding /> Şirket Adı
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      value={profileData.company_name}
                      onChange={(e) => setProfileData({...profileData, company_name: e.target.value})}
                      placeholder="Şirket adınız"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="form-label">
                      <FaIdCard /> VKN/TC Kimlik No *
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      value={profileData.vkn_tckn}
                      readOnly
                      disabled
                      style={{ backgroundColor: '#f5f5f5', cursor: 'not-allowed' }}
                      title="VKN/TC Kimlik numarası değiştirilemez"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="form-label">
                      <FaBuilding /> Vergi Dairesi
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      value={profileData.tax_office}
                      onChange={(e) => setProfileData({...profileData, tax_office: e.target.value})}
                      placeholder="Vergi daireniz"
                    />
                  </div>
                </div>
                
                <div className="form-group">
                  <label className="form-label">
                    <FaMapMarkerAlt /> Adres
                  </label>
                  <textarea
                    className="form-textarea"
                    value={profileData.address}
                    onChange={(e) => setProfileData({...profileData, address: e.target.value})}
                    placeholder="Adres bilgileriniz"
                    rows="3"
                  />
                </div>
              </div>

              <div className="form-actions">
                <LoadingButton
                  type="submit"
                  loading={updateProfileMutation.isPending}
                  variant="primary"
                  icon={<FaSave />}
                  loadingText="Kaydediliyor..."
                >
                  Değişiklikleri Kaydet
                </LoadingButton>
              </div>
            </form>
          )}

          {activeTab === 'password' && (
            <form onSubmit={handlePasswordSubmit} className="profile-form">
              <div className="form-section">
                <h3>Şifre Değiştir</h3>
                <p className="section-description">
                  Hesap güvenliğiniz için güçlü bir şifre seçin. Şifreniz en az 6 karakter olmalıdır.
                </p>
                
                <div className="form-group">
                  <label className="form-label">
                    <FaLock /> Mevcut Şifre *
                  </label>
                  <input
                    type="password"
                    className="form-input"
                    value={passwordData.current_password}
                    onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})}
                    placeholder="Mevcut şifrenizi girin"
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label">
                    <FaLock /> Yeni Şifre *
                  </label>
                  <input
                    type="password"
                    className="form-input"
                    value={passwordData.new_password}
                    onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                    placeholder="Yeni şifrenizi girin (en az 6 karakter)"
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label">
                    <FaLock /> Yeni Şifre Tekrar *
                  </label>
                  <input
                    type="password"
                    className="form-input"
                    value={passwordData.confirm_password}
                    onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                    placeholder="Yeni şifrenizi tekrar girin"
                    required
                  />
                </div>
              </div>

              <div className="form-actions">
                <LoadingButton
                  type="submit"
                  loading={changePasswordMutation.isPending}
                  variant="primary"
                  icon={<FaLock />}
                  loadingText="Değiştiriliyor..."
                >
                  Şifreyi Değiştir
                </LoadingButton>
              </div>
            </form>
          )}

          {activeTab === 'bayiler' && (
            <div className="bayiler-container">
              <div className="form-section">
                <h3>🏪 Bayilerim</h3>
                <p className="section-description">
                  VKN'nize kayıtlı tüm bayiler ve şubeleriniz burada listelenmektedir.
                </p>
                
                {bayilerLoading ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: '#95a5a6' }}>
                    <p>Bayiler yükleniyor...</p>
                  </div>
                ) : !bayilerData || bayilerData.bayiler?.length === 0 ? (
                  <div style={{ 
                    textAlign: 'center', 
                    padding: '40px', 
                    backgroundColor: '#f8f9fa', 
                    borderRadius: '8px',
                    border: '1px dashed #dee2e6'
                  }}>
                    <FaStore style={{ fontSize: '48px', color: '#ced4da', marginBottom: '16px' }} />
                    <p style={{ color: '#6c757d', margin: 0 }}>
                      VKN'nize kayıtlı bayi bulunamadı
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Özet Bilgiler */}
                    <div className="bayiler-summary" style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                      gap: '16px',
                      marginBottom: '24px'
                    }}>
                      <div style={{
                        backgroundColor: '#e3f2fd',
                        padding: '16px',
                        borderRadius: '8px',
                        border: '1px solid #90caf9'
                      }}>
                        <p style={{ margin: '0 0 4px 0', fontSize: '13px', color: '#1976d2' }}>Toplam Bayi</p>
                        <h3 style={{ margin: 0, color: '#1565c0' }}>{bayilerData.toplam_bayi_sayisi}</h3>
                      </div>
                      <div style={{
                        backgroundColor: '#f3e5f5',
                        padding: '16px',
                        borderRadius: '8px',
                        border: '1px solid #ce93d8'
                      }}>
                        <p style={{ margin: '0 0 4px 0', fontSize: '13px', color: '#7b1fa2' }}>VKN</p>
                        <h3 style={{ margin: 0, color: '#6a1b9a', fontSize: '16px' }}>{bayilerData.vkn_tckn}</h3>
                      </div>
                      <div style={{
                        backgroundColor: '#e8f5e9',
                        padding: '16px',
                        borderRadius: '8px',
                        border: '1px solid #81c784'
                      }}>
                        <p style={{ margin: '0 0 4px 0', fontSize: '13px', color: '#388e3c' }}>Toplam Bakiye</p>
                        <h3 style={{ margin: 0, color: '#2e7d32' }}>
                          {bayilerData.toplam_bakiye?.toLocaleString('tr-TR', { 
                            style: 'currency', 
                            currency: 'TRY' 
                          }) || '0,00 ₺'}
                        </h3>
                      </div>
                    </div>

                    {/* Bayiler Listesi */}
                    <div className="bayiler-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {bayilerData.bayiler?.map((bayi) => (
                        <div
                          key={bayi.id}
                          style={{
                            backgroundColor: '#fff',
                            border: '1px solid #dee2e6',
                            borderRadius: '8px',
                            padding: '16px',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            transition: 'all 0.2s',
                            cursor: 'pointer'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)'
                            e.currentTarget.style.borderColor = '#007bff'
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.boxShadow = 'none'
                            e.currentTarget.style.borderColor = '#dee2e6'
                          }}
                        >
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                              <FaStore style={{ color: '#007bff' }} />
                              <h4 style={{ margin: 0, fontSize: '16px', color: '#212529' }}>
                                {bayi.bayi_adi}
                              </h4>
                            </div>
                            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                              <span style={{ fontSize: '13px', color: '#6c757d' }}>
                                <strong>Kod:</strong> {bayi.bayi_kodu}
                              </span>
                              {bayi.donem && (
                                <span style={{ fontSize: '13px', color: '#6c757d' }}>
                                  <strong>Dönem:</strong> {bayi.donem}
                                </span>
                              )}
                            </div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <p style={{ 
                              margin: '0 0 4px 0', 
                              fontSize: '13px', 
                              color: '#6c757d' 
                            }}>
                              Bakiye
                            </p>
                            <h3 style={{ 
                              margin: 0, 
                              color: bayi.bakiye >= 0 ? '#28a745' : '#dc3545',
                              fontSize: '18px'
                            }}>
                              {bayi.bakiye?.toLocaleString('tr-TR', { 
                                style: 'currency', 
                                currency: 'TRY' 
                              }) || '0,00 ₺'}
                            </h3>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {activeTab === 'kvkk' && (
            <div className="kvkk-consents-view">
              <div className="form-section">
                <h3>🔒 KVKK Onaylarım</h3>
                <p className="section-description">
                  Kişisel Verilerin Korunması Kanunu (KVKK) kapsamında verdiğiniz onaylar ve detaylar aşağıda gösterilmektedir.
                </p>
              </div>

              {!kvkkConsent ? (
                <div className="kvkk-warning-box">
                  <FaExclamationTriangle style={{ fontSize: '48px', color: '#ff9800', marginBottom: '16px' }} />
                  <h3>KVKK Onaylarınız Alınmamış!</h3>
                  <p>
                    Sistemi kullanabilmek için KVKK onaylarınızı vermeniz gerekmektedir.
                    Lütfen çıkış yapıp tekrar giriş yaparak KVKK onaylarını tamamlayın.
                  </p>
                  <button
                    onClick={() => navigate('/')}
                    className="btn btn-primary"
                    style={{ marginTop: '16px' }}
                  >
                    Ana Sayfaya Dön
                  </button>
                </div>
              ) : (
                <div className="kvkk-consent-cards">
                  {/* 1. KVKK Politikası */}
                  <div className={`kvkk-consent-card ${kvkkConsent.kvkk_policy_accepted ? 'approved' : 'pending'}`}>
                    <div className="kvkk-consent-header">
                      <div className="kvkk-consent-icon">
                        {kvkkConsent.kvkk_policy_accepted ? (
                          <FaCheckCircle style={{ color: '#27ae60' }} />
                        ) : (
                          <FaClock style={{ color: '#95a5a6' }} />
                        )}
                      </div>
                      <div>
                        <h4>1. KVKK Politikası</h4>
                        <p>Kişisel verilerinizin korunması ve işlenmesi politikamız</p>
                      </div>
                    </div>
                    <div className="kvkk-consent-details">
                      {kvkkConsent.kvkk_policy_accepted ? (
                        <>
                          <div className="detail-row">
                            <span className="detail-label">Onay Tarihi:</span>
                            <span className="detail-value">
                              {new Date(kvkkConsent.kvkk_policy_date).toLocaleString('tr-TR')}
                            </span>
                          </div>
                          <div className="detail-row">
                            <span className="detail-label">Versiyon:</span>
                            <span className="detail-value">{kvkkConsent.kvkk_policy_version}</span>
                          </div>
                        </>
                      ) : (
                        <p style={{ color: '#95a5a6', fontSize: '14px', margin: 0 }}>Henüz onaylanmamış</p>
                      )}
                    </div>
                  </div>

                  {/* 2. Müşteri Aydınlatma Metni */}
                  <div className={`kvkk-consent-card ${kvkkConsent.customer_notice_accepted ? 'approved' : 'pending'}`}>
                    <div className="kvkk-consent-header">
                      <div className="kvkk-consent-icon">
                        {kvkkConsent.customer_notice_accepted ? (
                          <FaCheckCircle style={{ color: '#27ae60' }} />
                        ) : (
                          <FaClock style={{ color: '#95a5a6' }} />
                        )}
                      </div>
                      <div>
                        <h4>2. Müşteri Aydınlatma Metni</h4>
                        <p>Kişisel verilerinizin toplanması ve kullanımı hakkında bilgilendirme</p>
                      </div>
                    </div>
                    <div className="kvkk-consent-details">
                      {kvkkConsent.customer_notice_accepted ? (
                        <>
                          <div className="detail-row">
                            <span className="detail-label">Onay Tarihi:</span>
                            <span className="detail-value">
                              {new Date(kvkkConsent.customer_notice_date).toLocaleString('tr-TR')}
                            </span>
                          </div>
                          <div className="detail-row">
                            <span className="detail-label">Versiyon:</span>
                            <span className="detail-value">{kvkkConsent.customer_notice_version}</span>
                          </div>
                        </>
                      ) : (
                        <p style={{ color: '#95a5a6', fontSize: '14px', margin: 0 }}>Henüz onaylanmamış</p>
                      )}
                    </div>
                  </div>

                  {/* 3. Kişisel Veri Saklama ve İmha */}
                  <div className={`kvkk-consent-card ${kvkkConsent.data_retention_accepted ? 'approved' : 'pending'}`}>
                    <div className="kvkk-consent-header">
                      <div className="kvkk-consent-icon">
                        {kvkkConsent.data_retention_accepted ? (
                          <FaCheckCircle style={{ color: '#27ae60' }} />
                        ) : (
                          <FaClock style={{ color: '#95a5a6' }} />
                        )}
                      </div>
                      <div>
                        <h4>3. Kişisel Veri Saklama ve İmha Politikası</h4>
                        <p>Verilerinizin saklanma ve imha süreçleri</p>
                      </div>
                    </div>
                    <div className="kvkk-consent-details">
                      {kvkkConsent.data_retention_accepted ? (
                        <>
                          <div className="detail-row">
                            <span className="detail-label">Onay Tarihi:</span>
                            <span className="detail-value">
                              {new Date(kvkkConsent.data_retention_date).toLocaleString('tr-TR')}
                            </span>
                          </div>
                          <div className="detail-row">
                            <span className="detail-label">Versiyon:</span>
                            <span className="detail-value">{kvkkConsent.data_retention_version}</span>
                          </div>
                        </>
                      ) : (
                        <p style={{ color: '#95a5a6', fontSize: '14px', margin: 0 }}>Henüz onaylanmamış</p>
                      )}
                    </div>
                  </div>

                  {/* 4. E-Mutabakat Sistemi Kullanım Onayı */}
                  <div className={`kvkk-consent-card ${kvkkConsent.system_consent_accepted ? 'approved' : 'pending'} highlighted`}>
                    <div className="kvkk-consent-header">
                      <div className="kvkk-consent-icon">
                        {kvkkConsent.system_consent_accepted ? (
                          <FaCheckCircle style={{ color: '#27ae60' }} />
                        ) : (
                          <FaClock style={{ color: '#95a5a6' }} />
                        )}
                      </div>
                      <div>
                        <h4>4. E-Mutabakat Sistemi Kullanım Onayı ⚠️</h4>
                        <p>Sistem kullanımı ve yasal delil kayıtları</p>
                      </div>
                    </div>
                    <div className="kvkk-consent-details">
                      {kvkkConsent.system_consent_accepted ? (
                        <>
                          <div className="detail-row">
                            <span className="detail-label">Onay Tarihi:</span>
                            <span className="detail-value">
                              {new Date(kvkkConsent.system_consent_date).toLocaleString('tr-TR')}
                            </span>
                          </div>
                          <div className="detail-row">
                            <span className="detail-label">Versiyon:</span>
                            <span className="detail-value">{kvkkConsent.system_consent_version}</span>
                          </div>
                        </>
                      ) : (
                        <p style={{ color: '#95a5a6', fontSize: '14px', margin: 0 }}>Henüz onaylanmamış</p>
                      )}
                    </div>
                  </div>

                  {/* Yasal Delil Bilgileri */}
                  <div className="kvkk-legal-info">
                    <h4>📋 Yasal Delil Bilgileri</h4>
                    <p style={{ marginBottom: '16px', color: '#7f8c8d', fontSize: '14px' }}>
                      Onaylarınız aşağıdaki bilgilerle birlikte kaydedilmiştir:
                    </p>
                    <div className="legal-details-grid">
                      <div className="legal-detail">
                        <span className="legal-label">IP Adresi:</span>
                        <span className="legal-value">{kvkkConsent.ip_address || '-'}</span>
                      </div>
                      <div className="legal-detail">
                        <span className="legal-label">ISP:</span>
                        <span className="legal-value">{kvkkConsent.isp || '-'}</span>
                      </div>
                      <div className="legal-detail">
                        <span className="legal-label">Şehir:</span>
                        <span className="legal-value">{kvkkConsent.city || '-'}</span>
                      </div>
                      <div className="legal-detail">
                        <span className="legal-label">Ülke:</span>
                        <span className="legal-value">{kvkkConsent.country || '-'}</span>
                      </div>
                      <div className="legal-detail">
                        <span className="legal-label">Kayıt Tarihi:</span>
                        <span className="legal-value">
                          {new Date(kvkkConsent.created_at).toLocaleString('tr-TR')}
                        </span>
                      </div>
                    </div>
                    <p style={{ marginTop: '16px', fontSize: '13px', color: '#95a5a6', lineHeight: '1.6' }}>
                      ℹ️ Bu bilgiler 6698 sayılı Kişisel Verilerin Korunması Kanunu gereği yasal delil olarak 10 yıl süreyle saklanmaktadır.
                      Onaylarınızı geri çekmek veya değiştirmek için lütfen bizimle iletişime geçin.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

