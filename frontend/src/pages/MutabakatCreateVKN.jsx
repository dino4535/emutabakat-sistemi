import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'react-toastify'
import { FaSave, FaFileInvoice, FaTimesCircle, FaUsers } from 'react-icons/fa'
import './MutabakatCreate.css'

export default function MutabakatCreateManual() {
  const navigate = useNavigate()
  
  const [formData, setFormData] = useState({
    receiver_id: '',
    donem_baslangic: '',
    donem_bitis: '',
    bakiye: '',
    bakiye_turu: 'alacak', // 'alacak' veya 'borc'
    aciklama: ''
  })

  // Müşteri listesini çek (MUSTERI rolündeki kullanıcılar)
  const { data: customers, isLoading: customersLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: async () => {
      const response = await axios.get('/api/bulk-mutabakat/customers')
      return response.data
    },
    onError: (error) => {
      console.error('Müşteri listesi alınamadı:', error)
    }
  })

  // Mutabakat oluştur
  const createMutation = useMutation({
    mutationFn: async (data) => {
      // Bakiye türüne göre borç/alacak hesapla
      const bakiye_value = parseFloat(data.bakiye) || 0
      let toplam_borc = 0
      let toplam_alacak = 0

      if (data.bakiye_turu === 'alacak') {
        toplam_alacak = bakiye_value
      } else {
        toplam_borc = bakiye_value
      }

      const payload = {
        receiver_id: parseInt(data.receiver_id),
        donem_baslangic: new Date(data.donem_baslangic).toISOString(),
        donem_bitis: new Date(data.donem_bitis + 'T23:59:59').toISOString(),
        toplam_borc: toplam_borc,
        toplam_alacak: toplam_alacak,
        aciklama: data.aciklama || `${data.donem_baslangic} - ${data.donem_bitis} Dönemi Bakiye Mutabakatı`
      }

      console.log('Mutabakat oluşturma payload:', payload)
      const response = await axios.post('/api/mutabakat/', payload)
      return response.data
    },
    onSuccess: (data) => {
      toast.success('Mutabakat başarıyla oluşturuldu! (Taslak)')
      navigate('/mutabakat')
    },
    onError: (error) => {
      console.error('Mutabakat oluşturma hatası:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Mutabakat oluşturulamadı'
      toast.error(errorMsg)
    }
  })

  const handleSubmit = (e) => {
    e.preventDefault()

    // Validasyon
    if (!formData.receiver_id) {
      toast.error('Lütfen müşteri seçin')
      return
    }
    if (!formData.donem_baslangic || !formData.donem_bitis) {
      toast.error('Lütfen dönem tarihlerini girin')
      return
    }
    if (!formData.bakiye || parseFloat(formData.bakiye) <= 0) {
      toast.error('Lütfen geçerli bir bakiye girin')
      return
    }

    // Tarih kontrolü
    if (new Date(formData.donem_baslangic) > new Date(formData.donem_bitis)) {
      toast.error('Dönem başlangıç tarihi, bitiş tarihinden sonra olamaz')
      return
    }

    createMutation.mutate(formData)
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleCancel = () => {
    if (window.confirm('İptal etmek istediğinizden emin misiniz? Girdiğiniz veriler kaybolacak.')) {
      navigate('/mutabakat')
    }
  }

  // Bugünün tarihini YYYY-MM-DD formatında al
  const getTodayDate = () => {
    const today = new Date()
    return today.toISOString().split('T')[0]
  }

  // Önceki ayın ilk gününü al
  const getLastMonthFirstDay = () => {
    const date = new Date()
    date.setMonth(date.getMonth() - 1)
    date.setDate(1)
    return date.toISOString().split('T')[0]
  }

  // Önceki ayın son gününü al
  const getLastMonthLastDay = () => {
    const date = new Date()
    date.setDate(0) // Bir önceki ayın son günü
    return date.toISOString().split('T')[0]
  }

  return (
    <div className="mutabakat-create">
      <div className="page-header">
        <h1><FaFileInvoice /> Manuel Mutabakat Oluştur</h1>
        <p>Bakiye mutabakatı oluşturmak için tüm bilgileri manuel olarak girin</p>
      </div>

      <div className="create-form-container">
        <form onSubmit={handleSubmit} className="mutabakat-form">
          {/* Müşteri Seçimi */}
          <div className="form-section">
            <h3><FaUsers /> 1. Müşteri Seçimi</h3>
            <div className="form-group">
              <label className="required">Müşteri</label>
              <select
                name="receiver_id"
                value={formData.receiver_id}
                onChange={handleInputChange}
                required
                disabled={customersLoading}
                className="form-select"
              >
                <option value="">Müşteri seçiniz...</option>
                {customers && customers.map(customer => (
                  <option key={customer.id} value={customer.id}>
                    {customer.company_name || customer.full_name} 
                    {customer.vkn_tckn ? ` (${customer.vkn_tckn})` : ''}
                  </option>
                ))}
              </select>
              {customersLoading && <small className="text-muted">Müşteriler yükleniyor...</small>}
              {customers && customers.length === 0 && (
                <small className="text-warning">⚠️ Hiç müşteri bulunamadı</small>
              )}
            </div>
          </div>

          {/* Dönem Bilgileri */}
          <div className="form-section">
            <h3>2. Dönem Bilgileri</h3>
            <div className="form-row">
              <div className="form-group">
                <label className="required">Dönem Başlangıç</label>
                <input
                  type="date"
                  name="donem_baslangic"
                  value={formData.donem_baslangic}
                  onChange={handleInputChange}
                  max={getTodayDate()}
                  required
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label className="required">Dönem Bitiş</label>
                <input
                  type="date"
                  name="donem_bitis"
                  value={formData.donem_bitis}
                  onChange={handleInputChange}
                  max={getTodayDate()}
                  min={formData.donem_baslangic}
                  required
                  className="form-input"
                />
              </div>
            </div>
            <div className="quick-date-buttons">
              <button
                type="button"
                className="btn-quick-date"
                onClick={() => {
                  setFormData(prev => ({
                    ...prev,
                    donem_baslangic: getLastMonthFirstDay(),
                    donem_bitis: getLastMonthLastDay()
                  }))
                  toast.info('Geçen ay dönemi seçildi')
                }}
              >
                📅 Geçen Ay
              </button>
              <button
                type="button"
                className="btn-quick-date"
                onClick={() => {
                  const today = getTodayDate()
                  const firstDay = new Date()
                  firstDay.setDate(1)
                  setFormData(prev => ({
                    ...prev,
                    donem_baslangic: firstDay.toISOString().split('T')[0],
                    donem_bitis: today
                  }))
                  toast.info('Bu ay dönemi seçildi')
                }}
              >
                📅 Bu Ay
              </button>
            </div>
          </div>

          {/* Bakiye Bilgisi */}
          <div className="form-section">
            <h3>3. Bakiye Bilgisi</h3>
            <div className="bakiye-section">
              <div className="form-group">
                <label className="required">Bakiye Türü</label>
                <div className="radio-group">
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="bakiye_turu"
                      value="alacak"
                      checked={formData.bakiye_turu === 'alacak'}
                      onChange={handleInputChange}
                    />
                    <span className="radio-text">Alacak (Müşterinin Borcu)</span>
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="bakiye_turu"
                      value="borc"
                      checked={formData.bakiye_turu === 'borc'}
                      onChange={handleInputChange}
                    />
                    <span className="radio-text">Borç (Bizim Borcumuz)</span>
                  </label>
                </div>
              </div>
              <div className="form-group">
                <label className="required">Bakiye Tutarı (₺)</label>
                <input
                  type="number"
                  name="bakiye"
                  value={formData.bakiye}
                  onChange={handleInputChange}
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                  required
                  className="form-input bakiye-input"
                />
                <small className="bakiye-preview">
                  {formData.bakiye && parseFloat(formData.bakiye) > 0 ? (
                    formData.bakiye_turu === 'alacak' ? (
                      <span className="text-success">
                        ✅ Müşteri {parseFloat(formData.bakiye).toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺ borçlu
                      </span>
                    ) : (
                      <span className="text-danger">
                        ❌ Biz {parseFloat(formData.bakiye).toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺ borçluyuz
                      </span>
                    )
                  ) : (
                    <span className="text-muted">Bakiye tutarını girin</span>
                  )}
                </small>
              </div>
            </div>
          </div>

          {/* Açıklama */}
          <div className="form-section">
            <h3>4. Açıklama (Opsiyonel)</h3>
            <div className="form-group">
              <label>Açıklama</label>
              <textarea
                name="aciklama"
                value={formData.aciklama}
                onChange={handleInputChange}
                placeholder="Mutabakat ile ilgili açıklama..."
                rows={4}
                className="form-textarea"
              />
              <small className="text-muted">
                Boş bırakılırsa otomatik açıklama oluşturulacaktır
              </small>
            </div>
          </div>

          {/* Bilgilendirme */}
          <div className="info-box">
            <h4>ℹ️ Bilgilendirme</h4>
            <ul>
              <li>Bu mutabakat <strong>TASLAK</strong> olarak oluşturulacaktır</li>
              <li>Mutabakat listesinden <strong>gönder</strong> butonuna tıklayarak müşteriye e-posta gönderebilirsiniz</li>
              <li>Mutabakat türü: <strong>Bakiye Mutabakatı</strong> (Kalemsiz)</li>
              <li>Müşteri, e-posta ile gelen linke tıklayarak mutabakatı onaylayabilir veya reddedebilir</li>
            </ul>
          </div>

          {/* Form Butonları */}
          <div className="form-actions">
            <button
              type="button"
              className="btn btn-cancel"
              onClick={handleCancel}
              disabled={createMutation.isPending}
            >
              <FaTimesCircle /> İptal
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={createMutation.isPending || !formData.receiver_id}
            >
              <FaSave />
              {createMutation.isPending ? 'Oluşturuluyor...' : 'Mutabakat Oluştur (Taslak)'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
