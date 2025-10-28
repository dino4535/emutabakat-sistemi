import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { toast } from 'react-toastify'
import { FaEnvelope, FaLock, FaUser, FaBuilding, FaPhone } from 'react-icons/fa'
import './Auth.css'

export default function Register() {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
    company_name: '',
    tax_number: '',
    phone: '',
    role: 'musteri'
  })
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      await register(formData)
      toast.success('Kayıt başarılı! Giriş yapabilirsiniz.')
      navigate('/login')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Kayıt olunamadı')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Kayıt Ol</h1>
          <p>Yeni hesap oluşturun</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                <FaEnvelope /> Email
              </label>
              <input
                type="email"
                name="email"
                className="form-input"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="email@example.com"
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <FaUser /> Kullanıcı Adı
              </label>
              <input
                type="text"
                name="username"
                className="form-input"
                value={formData.username}
                onChange={handleChange}
                required
                placeholder="kullanici123"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              <FaLock /> Şifre
            </label>
            <input
              type="password"
              name="password"
              className="form-input"
              value={formData.password}
              onChange={handleChange}
              required
              minLength="6"
              placeholder="En az 6 karakter"
            />
          </div>

          <div className="form-group">
            <label className="form-label">
              <FaUser /> Ad Soyad
            </label>
            <input
              type="text"
              name="full_name"
              className="form-input"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="Ad Soyad"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                <FaBuilding /> Şirket Adı
              </label>
              <input
                type="text"
                name="company_name"
                className="form-input"
                value={formData.company_name}
                onChange={handleChange}
                placeholder="ABC Ltd. Şti."
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                Vergi No
              </label>
              <input
                type="text"
                name="tax_number"
                className="form-input"
                value={formData.tax_number}
                onChange={handleChange}
                placeholder="1234567890"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              <FaPhone /> Telefon
            </label>
            <input
              type="tel"
              name="phone"
              className="form-input"
              value={formData.phone}
              onChange={handleChange}
              placeholder="0555 123 4567"
            />
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Kayıt yapılıyor...' : 'Kayıt Ol'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Zaten hesabınız var mı?{' '}
            <Link to="/login" className="auth-link">
              Giriş Yap
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

