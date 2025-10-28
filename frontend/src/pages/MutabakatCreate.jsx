import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'react-toastify'
import { FaSave, FaFileInvoice } from 'react-icons/fa'
import './MutabakatCreate.css'

export default function MutabakatCreate() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    receiver_id: '',
    donem_baslangic: '',
    donem_bitis: '',
    toplam_borc: '',
    toplam_alacak: '',
    aciklama: ''
  })

  // Kullanıcıları al (müşteri/tedarikçi seçimi için)
  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await axios.get('/api/auth/users')
      return response.data
    }
  })

  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await axios.post('/api/mutabakat/', data)
      return response.data
    },
    onSuccess: () => {
      toast.success('Mutabakat başarıyla oluşturuldu!')
      navigate('/mutabakat')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Mutabakat oluşturulamadı')
    }
  })

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    // Validation
    if (!formData.receiver_id || !formData.donem_baslangic || !formData.donem_bitis) {
      toast.error('Lütfen gerekli alanları doldurun')
      return
    }

    const submitData = {
      receiver_id: parseInt(formData.receiver_id),
      donem_baslangic: new Date(formData.donem_baslangic).toISOString(),
      donem_bitis: new Date(formData.donem_bitis).toISOString(),
      toplam_borc: parseFloat(formData.toplam_borc) || 0,
      toplam_alacak: parseFloat(formData.toplam_alacak) || 0,
      aciklama: formData.aciklama
    }

    createMutation.mutate(submitData)
  }

  // Bakiye hesapla
  const bakiye = (parseFloat(formData.toplam_alacak) || 0) - (parseFloat(formData.toplam_borc) || 0)

  // Müşteri ve tedarikçileri filtrele
  const customers = users?.filter(u => ['musteri', 'tedarikci'].includes(u.role)) || []

  return (
    <div className="mutabakat-create">
      <div className="page-header">
        <h1><FaFileInvoice /> Yeni Mutabakat Oluştur</h1>
        <p>Basit bakiye mutabakatı oluşturun</p>
      </div>

      <form onSubmit={handleSubmit} className="mutabakat-form">
        {/* Temel Bilgiler */}
        <div className="form-section">
          <h2>Temel Bilgiler</h2>
          
          <div className="form-group">
            <label>Alıcı (Müşteri/Tedarikçi) *</label>
            <select
              name="receiver_id"
              value={formData.receiver_id}
              onChange={handleInputChange}
              required
            >
              <option value="">Seçiniz...</option>
              {customers.map(user => (
                <option key={user.id} value={user.id}>
                  {user.company_name || user.full_name || user.username}
                </option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Dönem Başlangıç *</label>
              <input
                type="date"
                name="donem_baslangic"
                value={formData.donem_baslangic}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Dönem Bitiş *</label>
              <input
                type="date"
                name="donem_bitis"
                value={formData.donem_bitis}
                onChange={handleInputChange}
                required
              />
            </div>
          </div>
        </div>

        {/* Bakiye Bilgileri */}
        <div className="form-section">
          <h2>Bakiye Bilgileri</h2>
          
          <div className="form-row">
            <div className="form-group">
              <label>Toplam Borç (₺)</label>
              <input
                type="number"
                step="0.01"
                name="toplam_borc"
                value={formData.toplam_borc}
                onChange={handleInputChange}
                placeholder="0.00"
              />
            </div>

            <div className="form-group">
              <label>Toplam Alacak (₺)</label>
              <input
                type="number"
                step="0.01"
                name="toplam_alacak"
                value={formData.toplam_alacak}
                onChange={handleInputChange}
                placeholder="0.00"
              />
            </div>
          </div>

          {/* Bakiye Özeti */}
          <div className="bakiye-ozet">
            <div className="bakiye-item">
              <span>Borç:</span>
              <strong className="borc">{parseFloat(formData.toplam_borc || 0).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY' })}</strong>
            </div>
            <div className="bakiye-item">
              <span>Alacak:</span>
              <strong className="alacak">{parseFloat(formData.toplam_alacak || 0).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY' })}</strong>
            </div>
            <div className="bakiye-item bakiye-total">
              <span>Bakiye:</span>
              <strong className={bakiye >= 0 ? 'positive' : 'negative'}>
                {bakiye.toLocaleString('tr-TR', { style: 'currency', currency: 'TRY' })}
              </strong>
            </div>
          </div>
        </div>

        {/* Açıklama */}
        <div className="form-section">
          <h2>Açıklama</h2>
          
          <div className="form-group">
            <label>Açıklama / Notlar</label>
            <textarea
              name="aciklama"
              value={formData.aciklama}
              onChange={handleInputChange}
              rows="4"
              placeholder="Opsiyonel not ekleyebilirsiniz..."
            />
          </div>
        </div>

        {/* Butonlar */}
        <div className="form-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/mutabakat')}
          >
            İptal
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={createMutation.isLoading}
          >
            <FaSave /> {createMutation.isLoading ? 'Kaydediliyor...' : 'Mutabakat Oluştur'}
          </button>
        </div>
      </form>

      {/* Bilgilendirme */}
      <div className="info-box">
        <h4>💡 Basit Bakiye Mutabakatı</h4>
        <p>Sadece toplam borç ve alacak tutarlarını girerek hızlıca mutabakat oluşturabilirsiniz.</p>
        <p>Müşteri/Tedarikçi red ederse, detaylı cari ekstre talep edebilir.</p>
      </div>
    </div>
  )
}
