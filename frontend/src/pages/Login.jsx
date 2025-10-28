import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { toast } from 'react-toastify'
import { FaEnvelope, FaLock, FaBuilding, FaChevronRight } from 'react-icons/fa'
import axios from 'axios'
import './Auth.css'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  
  // Multi-Company: Firma seçim ekranı için state'ler
  const [showCompanySelection, setShowCompanySelection] = useState(false)
  const [companies, setCompanies] = useState([])
  const [vknTckn, setVknTckn] = useState('')
  
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Backend'e login isteği at
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)
      
      const response = await axios.post('/api/auth/login', formData)
      
      // DURUM 1: Birden fazla şirket → Firma seçim ekranı göster
      if (response.data.requires_company_selection) {
        setCompanies(response.data.companies)
        setVknTckn(response.data.vkn_tckn)
        setShowCompanySelection(true)
        setLoading(false)
        toast.info('Lütfen giriş yapmak istediğiniz şirketi seçin')
        return
      }
      
      // DURUM 2: Tek şirket → Normal login devam
      const { access_token, ilk_giris_tamamlandi, vkn_tckn } = response.data
      localStorage.setItem('token', access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      await login(username, password)
      toast.success('Giriş başarılı!')
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Giriş yapılamadı')
      setLoading(false)
    }
  }
  
  const handleCompanySelect = async (companyId) => {
    setLoading(true)
    
    try {
      const response = await axios.post('/api/auth/login/select-company', {
        vkn_tckn: vknTckn,
        company_id: companyId,
        password: password
      })
      
      const { access_token, ilk_giris_tamamlandi, vkn_tckn } = response.data
      
      // Token'ı kaydet
      localStorage.setItem('token', access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      // Kullanıcı bilgilerini al (AuthContext'i güncelle)
      const userResponse = await axios.get('/api/auth/me')
      
      toast.success('Giriş başarılı!')
      
      // Full page reload ile AuthContext'in güncellendiğinden emin ol
      if (!ilk_giris_tamamlandi) {
        window.location.href = '/first-login'
      } else {
        window.location.href = '/dashboard'
      }
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Şirket seçimi başarısız')
      setLoading(false)
    }
  }

  // Firma seçim ekranını göster
  if (showCompanySelection) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <img 
              src="/dino-logo.png" 
              alt="Dino Gıda Logo" 
              style={{ 
                width: '120px', 
                height: 'auto', 
                marginBottom: '20px',
                display: 'block',
                marginLeft: 'auto',
                marginRight: 'auto'
              }} 
            />
            <h1>Şirket Seçimi</h1>
            <p>Hangi şirket olarak giriş yapmak istiyorsunuz?</p>
          </div>

          <div className="company-selection-container">
            {companies.map((company) => (
              <div 
                key={company.company_id}
                className="company-card-select"
                onClick={() => handleCompanySelect(company.company_id)}
                style={{ cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1 }}
              >
                <div className="company-logo-container">
                  {company.logo_path ? (
                    <img 
                      src={`/${company.logo_path.split('/').pop()}`} 
                      alt={company.company_name}
                      className="company-logo-img"
                      onError={(e) => {
                        e.target.style.display = 'none'
                        e.target.nextSibling.style.display = 'flex'
                      }}
                    />
                  ) : null}
                  <div className="company-icon" style={{ display: company.logo_path ? 'none' : 'flex' }}>
                    <FaBuilding />
                  </div>
                </div>
                <div className="company-info">
                  <h3>{company.company_name}</h3>
                  <p className="company-full-name">{company.full_company_name}</p>
                  {company.bayi_kodu && (
                    <p className="company-bayi-code">
                      <span className="badge-code">Bayi: {company.bayi_kodu}</span>
                    </p>
                  )}
                </div>
                <div className="company-arrow">
                  <FaChevronRight />
                </div>
              </div>
            ))}
          </div>

          <button 
            className="btn btn-secondary btn-block"
            onClick={() => {
              setShowCompanySelection(false)
              setCompanies([])
              setVknTckn('')
            }}
            disabled={loading}
          >
            Geri Dön
          </button>
        </div>
      </div>
    )
  }

  // Normal login ekranı
  return (
    <>
      
      <div className="auth-container">
        <div className="auth-card">
        <div className="auth-header">
          <img 
            src="/dino-logo.png" 
            alt="Dino Gıda Logo" 
            style={{ 
              width: '120px', 
              height: 'auto', 
              marginBottom: '20px',
              display: 'block',
              marginLeft: 'auto',
              marginRight: 'auto'
            }} 
          />
          <h1>E-Mutabakat Sistemi</h1>
          <p>Hesabınıza giriş yapın</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label className="form-label">
              <FaEnvelope /> Kullanıcı Adı
            </label>
            <input
              type="text"
              className="form-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="Kullanıcı adınızı girin"
            />
          </div>

          <div className="form-group">
            <label className="form-label">
              <FaLock /> Şifre
            </label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Şifrenizi girin"
            />
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Hesabınız yok mu?{' '}
            <Link to="/register" className="auth-link">
              Kayıt Ol
            </Link>
          </p>
        </div>
      </div>
    </div>
    </>
  )
}

