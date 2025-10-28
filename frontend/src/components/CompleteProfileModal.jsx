import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'react-toastify'
import { FaUser, FaPhone, FaEnvelope, FaTimes } from 'react-icons/fa'
import './CompleteProfileModal.css'

export default function CompleteProfileModal({ onComplete }) {
  const [formData, setFormData] = useState({
    phone: '',
    email: ''
  })

  const completeMutation = useMutation({
    mutationFn: async (data) => {
      const response = await axios.post('/api/auth/complete-profile', null, {
        params: {
          phone: data.phone,
          email: data.email
        }
      })
      return response.data
    },
    onSuccess: (data) => {
      toast.success('Profil bilgileriniz kaydedildi!')
      onComplete(data) // AuthContext'i güncelle
    },
    onError: (error) => {
      console.error('Profil tamamlama hatası:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Profil tamamlanamadı'
      toast.error(errorMsg)
    }
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Validasyon
    if (!formData.phone || !formData.email) {
      toast.error('Telefon ve email alanları zorunludur')
      return
    }

    // Telefon formatı kontrolü (basit)
    if (formData.phone.length < 10) {
      toast.error('Geçerli bir telefon numarası girin')
      return
    }

    // Email formatı kontrolü (basit)
    if (!formData.email.includes('@')) {
      toast.error('Geçerli bir email adresi girin')
      return
    }

    completeMutation.mutate(formData)
  }

  return (
    <div className="modal-overlay">
      <div className="modal-container profile-complete-modal">
        <div className="modal-header">
          <div className="modal-icon">
            <FaUser />
          </div>
          <h2>Profil Bilgilerinizi Tamamlayın</h2>
          <p>Devam etmek için lütfen aşağıdaki bilgileri doldurun</p>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="phone">
              <FaPhone /> Telefon Numarası *
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="0555 123 4567"
              required
              autoFocus
            />
            <small className="form-hint">
              SMS bildirimleri için kullanılacaktır
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="email">
              <FaEnvelope /> E-posta Adresi *
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="ornek@sirket.com"
              required
            />
            <small className="form-hint">
              Email bildirimleri için kullanılacaktır
            </small>
          </div>

          <div className="info-box">
            <FaEnvelope className="info-icon" />
            <div>
              <strong>Neden Bu Bilgiler Gerekli?</strong>
              <p>
                Mutabakat bildirimleri, onay linkleri ve sistem mesajları için
                telefon numaranız ve email adresiniz gereklidir.
              </p>
            </div>
          </div>

          <div className="modal-actions">
            <button 
              type="submit" 
              className="btn btn-primary btn-lg"
              disabled={completeMutation.isPending}
            >
              {completeMutation.isPending ? (
                <>
                  <span className="spinner"></span> Kaydediliyor...
                </>
              ) : (
                <>
                  Devam Et
                </>
              )}
            </button>
          </div>
        </form>

        <div className="modal-note">
          <small>
            * İşaretli alanlar zorunludur. Bu bilgiler güvenli bir şekilde saklanır.
          </small>
        </div>
      </div>
    </div>
  )
}

