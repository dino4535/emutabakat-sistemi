import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'react-toastify'
import { FaSave, FaFileInvoice, FaSearch, FaTimesCircle, FaCalculator } from 'react-icons/fa'
import './MutabakatCreate.css'

export default function MutabakatCreateByVKN() {
  const navigate = useNavigate()
  
  const [vknInput, setVknInput] = useState('')
  const [donem, setDonem] = useState({
    baslangic: '',
    bitis: ''
  })
  const [aciklama, setAciklama] = useState('')
  
  const [bayiData, setBayiData] = useState(null) // VKN'ye ait bayiler
  const [bayiBakiyeler, setBayiBakiyeler] = useState({}) // Her bayi için borç/alacak

  // VKN'ye göre bayileri getir
  const bayiQueryMutation = useMutation({
    mutationFn: async (vkn) => {
      const response = await axios.get(`/api/bayi/by-vkn/${vkn}`)
      return response.data
    },
    onSuccess: (data) => {
      setBayiData(data)
      
      // Default olarak mevcut bakiyelerini doldur
      const defaultBakiyeler = {}
      data.bayiler.forEach(bayi => {
        defaultBakiyeler[bayi.id] = {
          borc: bayi.bakiye > 0 ? bayi.bakiye : 0,
          alacak: bayi.bakiye < 0 ? Math.abs(bayi.bakiye) : 0
        }
      })
      setBayiBakiyeler(defaultBakiyeler)
      
      toast.success(`${data.toplam_bayi_sayisi} bayi bulundu!`)
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Bayi bulunamadı')
      setBayiData(null)
      setBayiBakiyeler({})
    }
  })

  // Mutabakat oluştur (VKN bazlı manuel)
  const createMutation = useMutation({
    mutationFn: async (payload) => {
      const response = await axios.post('/api/mutabakat/create-by-vkn-manual', payload)
      return response.data
    }
  })

  const handleSearchBayiler = () => {
    if (!vknInput.trim()) {
      toast.error('Lütfen VKN/TC Kimlik giriniz')
      return
    }

    if (vknInput.length !== 10 && vknInput.length !== 11) {
      toast.error('VKN 10 haneli, TC Kimlik 11 haneli olmalıdır')
      return
    }

    bayiQueryMutation.mutate(vknInput.trim())
  }

  const handleBakiyeChange = (bayiId, field, value) => {
    setBayiBakiyeler(prev => ({
      ...prev,
      [bayiId]: {
        ...prev[bayiId],
        [field]: value
      }
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    // Validasyon
    if (!bayiData || bayiData.bayiler.length === 0) {
      toast.error('Lütfen önce VKN ile bayi arayın')
      return
    }

    if (!donem.baslangic || !donem.bitis) {
      toast.error('Lütfen dönem tarihlerini giriniz')
      return
    }

    if (new Date(donem.baslangic) > new Date(donem.bitis)) {
      toast.error('Başlangıç tarihi bitiş tarihinden sonra olamaz')
      return
    }

    // Toplu mutabakat oluştur
    const toplamBorc = Object.values(bayiBakiyeler).reduce((sum, b) => sum + (parseFloat(b.borc) || 0), 0)
    const toplamAlacak = Object.values(bayiBakiyeler).reduce((sum, b) => sum + (parseFloat(b.alacak) || 0), 0)

    const payload = {
      receiver_vkn: vknInput.trim(),
      donem_baslangic: new Date(donem.baslangic).toISOString(),
      donem_bitis: new Date(donem.bitis + 'T23:59:59').toISOString(),
      toplam_borc: toplamBorc,
      toplam_alacak: toplamAlacak,
      aciklama: aciklama || `${bayiData.company_name} - ${donem.baslangic} / ${donem.bitis} Dönemi Mutabakatı`,
      bayiler: Object.entries(bayiBakiyeler).map(([bayiId, bakiye]) => ({
        bayi_id: parseInt(bayiId),
        borc: parseFloat(bakiye.borc) || 0,
        alacak: parseFloat(bakiye.alacak) || 0
      }))
    }

    try {
      await createMutation.mutateAsync(payload)
      toast.success('Mutabakat başarıyla oluşturuldu!')
      navigate('/mutabakat')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Mutabakat oluşturulamadı')
    }
  }

  const handleCancel = () => {
    if (window.confirm('İptal etmek istediğinizden emin misiniz?')) {
      navigate('/mutabakat')
    }
  }

  // Toplam bakiye hesapla
  const toplamBorc = Object.values(bayiBakiyeler).reduce((sum, b) => sum + (parseFloat(b.borc) || 0), 0)
  const toplamAlacak = Object.values(bayiBakiyeler).reduce((sum, b) => sum + (parseFloat(b.alacak) || 0), 0)
  const toplamBakiye = toplamAlacak - toplamBorc

  return (
    <div className="mutabakat-create">
      <div className="page-header">
        <h1><FaFileInvoice /> VKN Bazlı Mutabakat Oluştur</h1>
        <p>VKN/TC ile bayileri listeleyin ve bakiyelerini girerek mutabakat oluşturun</p>
      </div>

      <div className="create-form-container">
        {/* VKN Arama */}
        <div className="form-section">
          <h3><FaSearch /> 1. VKN/TC Kimlik ile Bayi Ara</h3>
          <div className="vkn-search-row">
            <div className="form-group" style={{ flex: 1 }}>
              <label>VKN / TC Kimlik Numarası</label>
              <input
                type="text"
                value={vknInput}
                onChange={(e) => setVknInput(e.target.value.replace(/\D/g, '').slice(0, 11))}
                placeholder="10 haneli VKN veya 11 haneli TC Kimlik"
                maxLength={11}
              />
            </div>
            <button
              type="button"
              className="btn-primary"
              onClick={handleSearchBayiler}
              disabled={bayiQueryMutation.isLoading}
            >
              <FaSearch /> {bayiQueryMutation.isLoading ? 'Aranıyor...' : 'Bayileri Getir'}
            </button>
          </div>
        </div>

        {/* Bayi Listesi */}
        {bayiData && (
          <>
            <div className="form-section">
              <h3><FaCalculator /> 2. Bayi Bakiyeleri ({bayiData.toplam_bayi_sayisi} Bayi)</h3>
              <div className="company-info-box">
                <div>
                  <strong>Şirket:</strong>
                  <span>{bayiData.company_name || vknInput}</span>
                </div>
                <div>
                  <strong>VKN:</strong>
                  <span>{bayiData.vkn_tckn}</span>
                </div>
                <div>
                  <strong>Toplam Bayi:</strong>
                  <span>{bayiData.toplam_bayi_sayisi} Adet</span>
                </div>
              </div>

              <div className="bayiler-table-container">
                <table className="bayiler-table">
                  <thead>
                    <tr>
                      <th>Bayi Kodu</th>
                      <th>Bayi Adı</th>
                      <th>Mevcut Bakiye</th>
                      <th>Borç (₺)</th>
                      <th>Alacak (₺)</th>
                      <th>Net Bakiye</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bayiData.bayiler.map(bayi => {
                      const borc = parseFloat(bayiBakiyeler[bayi.id]?.borc) || 0
                      const alacak = parseFloat(bayiBakiyeler[bayi.id]?.alacak) || 0
                      const netBakiye = alacak - borc

                      return (
                        <tr key={bayi.id}>
                          <td>{bayi.bayi_kodu}</td>
                          <td>{bayi.bayi_adi}</td>
                          <td className={bayi.bakiye > 0 ? 'borc' : bayi.bakiye < 0 ? 'alacak' : ''}>
                            {bayi.bakiye?.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺
                          </td>
                          <td>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={bayiBakiyeler[bayi.id]?.borc || ''}
                              onChange={(e) => handleBakiyeChange(bayi.id, 'borc', e.target.value)}
                              className="bakiye-input"
                            />
                          </td>
                          <td>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={bayiBakiyeler[bayi.id]?.alacak || ''}
                              onChange={(e) => handleBakiyeChange(bayi.id, 'alacak', e.target.value)}
                              className="bakiye-input"
                            />
                          </td>
                          <td className={netBakiye > 0 ? 'alacak' : netBakiye < 0 ? 'borc' : ''}>
                            {netBakiye.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {/* Toplamlar Kutusu */}
              <div className="bayiler-totals-box">
                <div className="totals-grid">
                  <div className="total-item">
                    <span className="total-label">Toplam Borç:</span>
                    <span className="total-value borc-color">
                      {toplamBorc.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺
                    </span>
                  </div>
                  <div className="total-item">
                    <span className="total-label">Toplam Alacak:</span>
                    <span className="total-value alacak-color">
                      {toplamAlacak.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺
                    </span>
                  </div>
                  <div className="total-item net-bakiye-item">
                    <span className="total-label">Net Bakiye:</span>
                    <span className={`total-value net-bakiye-value ${toplamBakiye > 0 ? 'alacak-color' : toplamBakiye < 0 ? 'borc-color' : ''}`}>
                      {toplamBakiye.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Dönem ve Açıklama */}
            <form onSubmit={handleSubmit}>
              <div className="form-section">
                <h3>3. Dönem ve Açıklama</h3>
                
                <div className="form-row">
                  <div className="form-group">
                    <label className="required">Dönem Başlangıç</label>
                    <input
                      type="date"
                      value={donem.baslangic}
                      onChange={(e) => setDonem(prev => ({ ...prev, baslangic: e.target.value }))}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="required">Dönem Bitiş</label>
                    <input
                      type="date"
                      value={donem.bitis}
                      onChange={(e) => setDonem(prev => ({ ...prev, bitis: e.target.value }))}
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Açıklama</label>
                  <textarea
                    value={aciklama}
                    onChange={(e) => setAciklama(e.target.value)}
                    placeholder="Mutabakat açıklaması (opsiyonel)"
                    rows={3}
                  />
                </div>
              </div>

              {/* Özet */}
              <div className="summary-box">
                <h3>Mutabakat Özeti</h3>
                <div className="summary-grid">
                  <div className="summary-item">
                    <span>Toplam Bayi Sayısı:</span>
                    <strong>{bayiData.toplam_bayi_sayisi}</strong>
                  </div>
                  <div className="summary-item">
                    <span>Toplam Borç:</span>
                    <strong className="borc">{toplamBorc.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺</strong>
                  </div>
                  <div className="summary-item">
                    <span>Toplam Alacak:</span>
                    <strong className="alacak">{toplamAlacak.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺</strong>
                  </div>
                  <div className="summary-item">
                    <span>Net Bakiye:</span>
                    <strong className={toplamBakiye > 0 ? 'alacak' : toplamBakiye < 0 ? 'borc' : ''}>
                      {toplamBakiye.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                    </strong>
                  </div>
                </div>
              </div>

              {/* Butonlar */}
              <div className="form-actions">
                <button
                  type="button"
                  onClick={handleCancel}
                  className="btn-secondary"
                >
                  <FaTimesCircle /> İptal
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={createMutation.isLoading}
                >
                  <FaSave /> {createMutation.isLoading ? 'Oluşturuluyor...' : 'Mutabakat Oluştur'}
                </button>
              </div>
            </form>
          </>
        )}

        {/* İlk durum mesajı */}
        {!bayiData && !bayiQueryMutation.isLoading && (
          <div className="empty-state">
            <FaSearch size={48} color="#ccc" />
            <p>VKN/TC Kimlik numarası girerek bayileri listeleyin</p>
          </div>
        )}
      </div>
    </div>
  )
}

