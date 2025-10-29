import { useState, useEffect } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'react-toastify'
import { FaCheckCircle, FaTimesCircle, FaShieldAlt, FaFileAlt, FaSearch, FaQrcode } from 'react-icons/fa'
import './VerifySignature.css'

export default function VerifySignature() {
  const location = useLocation()
  const { mutabakatNo: urlMutabakatNo } = useParams() // URL'den mutabakat no al
  const [activeTab, setActiveTab] = useState('manuel') // 'manuel' veya 'pdf'
  const [mutabakatNo, setMutabakatNo] = useState('')
  const [dijitalImza, setDijitalImza] = useState('')
  const [verificationResult, setVerificationResult] = useState(null)
  const [fromQR, setFromQR] = useState(false)
  const [pdfFile, setPdfFile] = useState(null)
  const [pdfVerificationResult, setPdfVerificationResult] = useState(null)
  const [mutabakatInfo, setMutabakatInfo] = useState(null)
  const [mutabakatLogs, setMutabakatLogs] = useState([])
  const [loadingInfo, setLoadingInfo] = useState(false)

  // Mutabakat bilgilerini getir
  const fetchMutabakatInfo = async (mutabakatNo) => {
    if (!mutabakatNo) return
    
    setLoadingInfo(true)
    try {
      const response = await axios.get(`/api/public/mutabakat/verify/${mutabakatNo}`)
      if (response.data.success) {
        setMutabakatInfo(response.data.mutabakat)
        setMutabakatLogs(response.data.logs)
      }
    } catch (error) {
      console.error('Mutabakat bilgileri alınamadı:', error)
      // Hata gösterme - public sayfada zorunlu değil
    } finally {
      setLoadingInfo(false)
    }
  }

  // URL parametrelerinden değerleri al (QR kod için)
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const qrMutabakatNo = urlMutabakatNo || params.get('mutabakat_no') // Path param veya query param
    const qrDijitalImza = params.get('dijital_imza')
    const qrHash = params.get('hash')
    
    // QR kod'dan geliyorsa (path param varsa)
    if (qrMutabakatNo) {
      setMutabakatNo(qrMutabakatNo)
      setFromQR(true)
      toast.info('QR kod ile mutabakat no yüklendi! PDF dosyasını yükleyerek doğrulayın.', { icon: '📱' })
      // QR kod'dan geldiğinde direkt PDF doğrulama tab'ına geç
      setActiveTab('pdf')
      
      // Mutabakat bilgilerini çek
      fetchMutabakatInfo(qrMutabakatNo)
    }
    
    // Eski format (query params ile dijital imza varsa)
    if (qrMutabakatNo && qrDijitalImza) {
      setMutabakatNo(qrMutabakatNo)
      setDijitalImza(qrDijitalImza)
      setFromQR(true)
      setActiveTab('manuel')
      toast.info('QR kod ile bilgiler yüklendi!', { icon: '📱' })
      
      // Mutabakat bilgilerini çek
      fetchMutabakatInfo(qrMutabakatNo)
      
      // Otomatik doğrulama (opsiyonel)
      setTimeout(() => {
        verifyMutation.mutate({
          mutabakat_no: qrMutabakatNo.trim(),
          dijital_imza: qrDijitalImza.trim()
        })
      }, 500)
    }
  }, [location.search, urlMutabakatNo])

  const verifyMutation = useMutation({
    mutationFn: async (data) => {
      const response = await axios.post('/api/verify/mutabakat', data)
      return response.data
    },
    onSuccess: (data) => {
      setVerificationResult(data)
      if (data.gecerli) {
        toast.success('Dijital imza doğrulandı!')
      } else {
        toast.error('Dijital imza geçersiz!')
      }
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Doğrulama işlemi başarısız')
      setVerificationResult(null)
    }
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (!mutabakatNo.trim()) {
      toast.error('Lütfen mutabakat numarasını girin')
      return
    }
    
    if (!dijitalImza.trim()) {
      toast.error('Lütfen dijital imzayı girin')
      return
    }

    verifyMutation.mutate({
      mutabakat_no: mutabakatNo.trim(),
      dijital_imza: dijitalImza.trim()
    })
  }

  const handleReset = () => {
    setMutabakatNo('')
    setDijitalImza('')
    setVerificationResult(null)
  }

  // PDF Upload Mutation
  const pdfVerifyMutation = useMutation({
    mutationFn: async (file) => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await axios.post('/api/verify/pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 30000 // 30 saniye timeout
      })
      return response.data
    },
    onSuccess: (data) => {
      setPdfVerificationResult(data)
      if (data.gecerli) {
        toast.success('PDF dosyası doğrulandı! Orijinal ve değiştirilmemiş.')
      } else {
        toast.error('PDF dosyası geçersiz veya değiştirilmiş!')
      }
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'PDF doğrulama başarısız')
      setPdfVerificationResult(null)
    }
  })

  const handlePdfUpload = (e) => {
    const file = e.target.files[0]
    if (file) {
      if (!file.name.endsWith('.pdf')) {
        toast.error('Lütfen PDF dosyası seçin')
        return
      }
      setPdfFile(file)
      setPdfVerificationResult(null)
      // Otomatik doğrulama başlat
      pdfVerifyMutation.mutate(file)
    }
  }

  const handlePdfReset = () => {
    setPdfFile(null)
    setPdfVerificationResult(null)
  }

  return (
    <div className="verify-signature public-page">
      {/* Public Sayfalar için Logo/Header */}
      <div className="public-header">
        <div className="logo-container">
          {mutabakatInfo && mutabakatInfo.company_logo ? (
            <img 
              src={`/${mutabakatInfo.company_logo}`}
              alt={mutabakatInfo.company_name} 
              className="company-logo" 
              onError={(e) => {
                // Logo yüklenemezse default logo göster
                console.error('Logo yüklenemedi:', mutabakatInfo.company_logo)
                e.target.src = '/dino-logo.png'
              }}
            />
          ) : (
            <img src="/dino-logo.png" alt="Logo" className="company-logo" />
          )}
          <h2>E-Mutabakat Sistemi</h2>
          {mutabakatInfo && (
            <p className="company-name">{mutabakatInfo.company_name}</p>
          )}
        </div>
      </div>

      <div className="verify-header">
        <div className="header-icon">
          <FaShieldAlt />
        </div>
        <h1>
          ⚖️ Dijital İmza Doğrulama 
          {fromQR && <span className="qr-badge"><FaQrcode /> QR Kod</span>}
        </h1>
        <p className="subtitle">
          {fromQR 
            ? "QR kod ile belge bilgileri otomatik yüklendi. PDF dosyasını yükleyerek doğrulayın." 
            : "Mutabakat belgelerinin dijital imzasını doğrulayarak belgenin orijinalliğini ve değiştirilmediğini matematiksel olarak kanıtlayabilirsiniz."
          }
        </p>
      </div>

      <div className="verify-content">
        {/* Mutabakat Özet Bilgileri */}
        {mutabakatInfo && (
          <div className="mutabakat-info-card">
            <div className="info-header">
              <h3>📋 Mutabakat Özet Bilgileri</h3>
              <span className={`status-badge status-${mutabakatInfo.durum}`}>
                {mutabakatInfo.durum}
              </span>
            </div>
            
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Mutabakat No:</span>
                <span className="info-value">{mutabakatInfo.mutabakat_no}</span>
              </div>
              
              <div className="info-item">
                <span className="info-label">Şirket:</span>
                <span className="info-value">{mutabakatInfo.company_name}</span>
              </div>
              
              <div className="info-item">
                <span className="info-label">VKN:</span>
                <span className="info-value">{mutabakatInfo.company_vkn}</span>
              </div>
              
              <div className="info-item">
                <span className="info-label">Dönem:</span>
                <span className="info-value">
                  {new Date(mutabakatInfo.donem_baslangic).toLocaleDateString('tr-TR')} - {new Date(mutabakatInfo.donem_bitis).toLocaleDateString('tr-TR')}
                </span>
              </div>
              
              <div className="info-item">
                <span className="info-label">Toplam Borç:</span>
                <span className="info-value amount-red">
                  {mutabakatInfo.toplam_borc?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                </span>
              </div>
              
              <div className="info-item">
                <span className="info-label">Toplam Alacak:</span>
                <span className="info-value amount-green">
                  {mutabakatInfo.toplam_alacak?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                </span>
              </div>
              
              <div className="info-item">
                <span className="info-label">Bakiye:</span>
                <span className={`info-value amount-${mutabakatInfo.bakiye >= 0 ? 'green' : 'red'}`}>
                  {mutabakatInfo.bakiye?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                </span>
              </div>
              
              <div className="info-item">
                <span className="info-label">Toplam Bayi:</span>
                <span className="info-value">{mutabakatInfo.toplam_bayi_sayisi}</span>
              </div>
              
              <div className="info-item full-width">
                <span className="info-label">Gönderen:</span>
                <span className="info-value">{mutabakatInfo.sender_name}</span>
              </div>
              
              <div className="info-item full-width">
                <span className="info-label">Alıcı:</span>
                <span className="info-value">{mutabakatInfo.receiver_name} ({mutabakatInfo.receiver_vkn})</span>
              </div>
              
              {mutabakatInfo.aciklama && (
                <div className="info-item full-width">
                  <span className="info-label">Açıklama:</span>
                  <span className="info-value">{mutabakatInfo.aciklama}</span>
                </div>
              )}
            </div>

            {/* Bayi Detayları */}
            {mutabakatInfo.bayi_detaylari && mutabakatInfo.bayi_detaylari.length > 0 && (
              <div className="bayi-detaylari-section">
                <h4>🏪 Bayi Detayları ({mutabakatInfo.bayi_detaylari.length} Bayi)</h4>
                <div className="table-responsive">
                  <table className="bayi-table">
                    <thead>
                      <tr>
                        <th>Bayi Kodu</th>
                        <th>Bayi Adı</th>
                        <th className="text-right">Bakiye</th>
                      </tr>
                    </thead>
                    <tbody>
                      {mutabakatInfo.bayi_detaylari.map((bayi, index) => (
                        <tr key={index}>
                          <td>{bayi.bayi_kodu}</td>
                          <td>{bayi.bayi_adi}</td>
                          <td className={`text-right ${bayi.bakiye < 0 ? 'negative' : 'positive'}`}>
                            {bayi.bakiye.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr>
                        <td colSpan="2"><strong>TOPLAM</strong></td>
                        <td className={`text-right ${mutabakatInfo.bakiye < 0 ? 'negative' : 'positive'}`}>
                          <strong>{mutabakatInfo.bakiye?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺</strong>
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            )}
            
            <div className="compare-message">
              <FaSearch />
              <strong>Lütfen PDF'deki bilgilerle yukarıdaki bilgileri karşılaştırın!</strong>
              <p>PDF ile veritabanındaki bilgiler aynı olmalıdır.</p>
            </div>
          </div>
        )}

        {/* İşlem Logları */}
        {mutabakatLogs && mutabakatLogs.length > 0 && (
          <div className="logs-card">
            <h3>📝 İşlem Geçmişi ve Dijital Deliller</h3>
            <div className="logs-timeline">
              {mutabakatLogs.map((log, index) => (
                <div key={index} className="log-item">
                  <div className="log-icon">
                    {log.action.includes('OLUSTUR') && '📝'}
                    {log.action.includes('ONAYLA') && '✅'}
                    {log.action.includes('REDDET') && '❌'}
                    {log.action.includes('GONDER') && '📤'}
                    {!log.action.includes('OLUSTUR') && !log.action.includes('ONAYLA') && !log.action.includes('REDDET') && !log.action.includes('GONDER') && '📋'}
                  </div>
                  <div className="log-content">
                    <div className="log-header">
                      <strong>{log.description}</strong>
                      <span className="log-time">
                        {new Date(log.created_at).toLocaleString('tr-TR')}
                      </span>
                    </div>
                    <div className="log-details">
                      <span className="log-user">👤 {log.full_name} (@{log.username})</span>
                      <span className="log-ip">🌐 IP: {log.ip_address}</span>
                      {log.isp && <span className="log-isp">📡 ISP: {log.isp}</span>}
                      {log.city && log.country && (
                        <span className="log-location">📍 {log.city}, {log.country}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="logs-info">
              <FaShieldAlt />
              <small>Bu bilgiler değiştirilemez delillerdir ve yasal süreçlerde kullanılabilir.</small>
            </div>
          </div>
        )}

        {/* Loading durumu */}
        {loadingInfo && (
          <div className="loading-box">
            <div className="spinner"></div>
            <p>Mutabakat bilgileri yükleniyor...</p>
          </div>
        )}

        {/* QR kod'dan geliyorsa doğrulama formlarını gösterme */}
        {fromQR && mutabakatInfo && (
          <div className="info-card qr-info">
            <h3>✅ Mutabakat Bilgileri Doğrulandı</h3>
            <p>
              Bu sayfa QR kod üzerinden açıldı. Mutabakat bilgileri yukarıda görüntülenmektedir.
              Lütfen PDF'deki bilgilerle yukarıdaki bilgileri karşılaştırın.
            </p>
            <div className="success-box">
              🔒 <strong>Güvenlik:</strong> Tüm işlem logları ve dijital deliller yukarıda listelenmiştir.
            </div>
          </div>
        )}

        {/* Tab Seçim Butonları - Sadece QR'dan gelmiyorsa göster */}
        {!fromQR && (
          <>
            <div className="verification-tabs">
              <button
                className={`tab-btn ${activeTab === 'manuel' ? 'active' : ''}`}
                onClick={() => setActiveTab('manuel')}
              >
                <FaSearch /> Manuel Doğrulama
              </button>
              <button
                className={`tab-btn ${activeTab === 'pdf' ? 'active' : ''}`}
                onClick={() => setActiveTab('pdf')}
              >
                <FaFileAlt /> PDF Dosyası ile Doğrulama (Önerilen)
              </button>
            </div>

        {/* Manuel Doğrulama Tab */}
        {activeTab === 'manuel' && (
          <>
            <div className="info-card">
              <h3>📋 Manuel Doğrulama</h3>
              <ol>
                <li>PDF mutabakat belgesini açın</li>
                <li>Belgenin en altında yer alan <strong>Mutabakat No</strong> ve <strong>Dijital İmza</strong> bilgilerini kopyalayın</li>
                <li>Aşağıdaki formu doldurun ve <strong>Doğrula</strong> butonuna tıklayın</li>
              </ol>
              <div className="warning-box">
                ⚠️ <strong>Uyarı:</strong> Manuel doğrulama sadece veritabanı kontrolü yapar. 
                PDF dosyasının değiştirilip değiştirilmediğini tespit edemez. 
                Daha güvenli doğrulama için <strong>"PDF Dosyası ile Doğrulama"</strong> seçeneğini kullanın.
              </div>
            </div>
          </>
        )}

        {/* PDF Doğrulama Tab */}
        {activeTab === 'pdf' && (
          <div className="info-card">
            <h3>📄 PDF Dosyası ile Doğrulama (GÜVENLİ)</h3>
            <ol>
              <li>PDF mutabakat belgenizi hazırlayın</li>
              <li>Aşağıdaki alana PDF dosyasını sürükleyin veya seçin</li>
              <li>Sistem otomatik olarak:
                <ul>
                  <li>✅ pyHanko dijital imzasını kontrol eder</li>
                  <li>✅ PDF'in değiştirilip değiştirilmediğini tespit eder</li>
                  <li>✅ Veritabanı ile hash karşılaştırması yapar</li>
                </ul>
              </li>
            </ol>
            <div className="success-box">
              🔒 <strong>Güvenli:</strong> Bu yöntem PDF üzerinde yapılan herhangi bir değişikliği tespit eder!
            </div>
          </div>
        )}

        {/* Manuel Doğrulama Formu */}
        {activeTab === 'manuel' && (
          <form onSubmit={handleSubmit} className="verify-form">
            <div className="form-section">
              <div className="form-group">
                <label htmlFor="mutabakat_no">
                  <FaFileAlt /> Mutabakat Numarası *
                </label>
                <input
                  type="text"
                  id="mutabakat_no"
                  value={mutabakatNo}
                  onChange={(e) => setMutabakatNo(e.target.value)}
                  placeholder="Örnek: MUT-20251020230253-I4MU"
                  disabled={verifyMutation.isPending}
                />
                <small className="help-text">
                  Mutabakat numarası PDF belgenizin üst kısmında yer alır
                </small>
              </div>

              <div className="form-group">
                <label htmlFor="dijital_imza">
                  <FaShieldAlt /> Dijital İmza (SHA-256) *
                </label>
                <textarea
                  id="dijital_imza"
                  value={dijitalImza}
                  onChange={(e) => setDijitalImza(e.target.value)}
                  placeholder="Örnek: 0432dca0be20ae0e124c9dc3a2aef39f8516d1267af184476a4d96b4b40abc8"
                  rows="3"
                  disabled={verifyMutation.isPending}
                />
                <small className="help-text">
                  Dijital imza PDF belgenizin en altında "Tam Dijital İmza (SHA-256)" başlığı altında yer alır
                </small>
              </div>
            </div>

            <div className="form-actions">
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={verifyMutation.isPending}
              >
                <FaSearch /> {verifyMutation.isPending ? 'Doğrulanıyor...' : 'Doğrula'}
              </button>
              
              {verificationResult && (
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={handleReset}
                >
                  Yeni Doğrulama
                </button>
              )}
            </div>
          </form>
        )}

        {/* PDF Upload Formu */}
        {activeTab === 'pdf' && (
          <div className="pdf-upload-section">
            <div className="upload-box">
              <input
                type="file"
                id="pdf-upload"
                accept=".pdf"
                onChange={handlePdfUpload}
                style={{ display: 'none' }}
              />
              <label htmlFor="pdf-upload" className="upload-label">
                <FaFileAlt className="upload-icon" />
                <h3>PDF Dosyasını Seçin veya Sürükleyin</h3>
                <p>
                  {pdfFile ? (
                    <span className="file-name">📄 {pdfFile.name}</span>
                  ) : (
                    'Mutabakat belgesi PDF dosyanızı buraya yükleyin'
                  )}
                </p>
                <button type="button" className="btn btn-upload">
                  Dosya Seç
                </button>
              </label>
            </div>

            {pdfFile && (
              <div className="form-actions">
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={handlePdfReset}
                >
                  Farklı Dosya Seç
                </button>
              </div>
            )}

            {pdfVerifyMutation.isPending && (
              <div className="loading-box">
                <div className="spinner"></div>
                <p>PDF dosyası doğrulanıyor...</p>
                <small>pyHanko dijital imza kontrolü yapılıyor</small>
              </div>
            )}
          </div>
        )}

        {verificationResult && (
          <div className={`verification-result ${verificationResult.gecerli ? 'valid' : 'invalid'}`}>
            <div className="result-header">
              {verificationResult.gecerli ? (
                <>
                  <FaCheckCircle className="icon-valid" />
                  <h2>✓ Dijital İmza GEÇERLİ</h2>
                </>
              ) : (
                <>
                  <FaTimesCircle className="icon-invalid" />
                  <h2>✗ Dijital İmza GEÇERSİZ</h2>
                </>
              )}
            </div>

            <div className="result-message">
              <p>{verificationResult.mesaj}</p>
            </div>

            {verificationResult.gecerli && verificationResult.mutabakat_no && (
              <div className="result-details">
                <h3>📊 Mutabakat Detayları</h3>
                
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">Mutabakat No:</span>
                    <span className="detail-value">{verificationResult.mutabakat_no}</span>
                  </div>

                  <div className="detail-item">
                    <span className="detail-label">Durum:</span>
                    <span className={`detail-value badge ${verificationResult.durum === 'Onaylandı' ? 'badge-success' : 'badge-danger'}`}>
                      {verificationResult.durum}
                    </span>
                  </div>

                  <div className="detail-item full-width">
                    <span className="detail-label">Gönderen Şirket:</span>
                    <span className="detail-value">{verificationResult.sender_company}</span>
                  </div>

                  <div className="detail-item full-width">
                    <span className="detail-label">Alıcı Şirket:</span>
                    <span className="detail-value">{verificationResult.receiver_company}</span>
                  </div>

                  <div className="detail-item">
                    <span className="detail-label">Toplam Borç:</span>
                    <span className="detail-value">{verificationResult.toplam_borc?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺</span>
                  </div>

                  <div className="detail-item">
                    <span className="detail-label">Toplam Alacak:</span>
                    <span className="detail-value">{verificationResult.toplam_alacak?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺</span>
                  </div>

                  <div className="detail-item">
                    <span className="detail-label">Net Bakiye:</span>
                    <span className={`detail-value ${verificationResult.bakiye < 0 ? 'negative' : 'positive'}`}>
                      {verificationResult.bakiye?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                    </span>
                  </div>

                  {verificationResult.onay_tarihi && (
                    <div className="detail-item">
                      <span className="detail-label">Onay Tarihi:</span>
                      <span className="detail-value">{verificationResult.onay_tarihi}</span>
                    </div>
                  )}

                  {verificationResult.red_tarihi && (
                    <div className="detail-item">
                      <span className="detail-label">Red Tarihi:</span>
                      <span className="detail-value">{verificationResult.red_tarihi}</span>
                    </div>
                  )}

                  {verificationResult.red_nedeni && (
                    <div className="detail-item full-width">
                      <span className="detail-label">Red Nedeni:</span>
                      <span className="detail-value">{verificationResult.red_nedeni}</span>
                    </div>
                  )}
                </div>

                {/* Bayi Detayları */}
                {verificationResult.bayi_detaylari && verificationResult.bayi_detaylari.length > 0 && (
                  <div className="bayi-detaylari-section">
                    <h4>🏪 Bayi Detayları ({verificationResult.bayi_detaylari.length} Bayi)</h4>
                    <div className="table-responsive">
                      <table className="bayi-table">
                        <thead>
                          <tr>
                            <th>Bayi Kodu</th>
                            <th>Bayi Adı</th>
                            <th className="text-right">Bakiye</th>
                          </tr>
                        </thead>
                        <tbody>
                          {verificationResult.bayi_detaylari.map((bayi, index) => (
                            <tr key={index}>
                              <td>{bayi.bayi_kodu}</td>
                              <td>{bayi.bayi_adi}</td>
                              <td className={`text-right ${bayi.bakiye < 0 ? 'negative' : 'positive'}`}>
                                {bayi.bakiye.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                              </td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot>
                          <tr>
                            <td colSpan="2"><strong>TOPLAM</strong></td>
                            <td className={`text-right ${verificationResult.bakiye < 0 ? 'negative' : 'positive'}`}>
                              <strong>{verificationResult.bakiye?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺</strong>
                            </td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  </div>
                )}

                <div className="legal-notice">
                  <h4>⚖️ Yasal Geçerlilik</h4>
                  <p>
                    Bu dijital imza, <strong>5070 sayılı Elektronik İmza Kanunu</strong> kapsamında 
                    yasal geçerliliğe sahiptir. Belgenin değiştirilmediği SHA-256 hash algoritması 
                    ile matematiksel olarak kanıtlanmıştır.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* PDF Doğrulama Sonucu */}
        {pdfVerificationResult && (
          <div className={`verification-result ${pdfVerificationResult.gecerli ? 'valid' : 'invalid'}`}>
            <div className="result-header">
              {pdfVerificationResult.gecerli ? (
                <>
                  <FaCheckCircle className="icon-valid" />
                  <h2>✓ PDF BELGESİ GEÇERLİ ve DEĞİŞTİRİLMEMİŞ</h2>
                </>
              ) : (
                <>
                  <FaTimesCircle className="icon-invalid" />
                  <h2>✗ PDF BELGESİ GEÇERSİZ veya DEĞİŞTİRİLMİŞ</h2>
                </>
              )}
            </div>

            <div className="result-body">
              <div className="result-message">
                <p>{pdfVerificationResult.mesaj}</p>
              </div>

              {pdfVerificationResult.uyarilar && pdfVerificationResult.uyarilar.length > 0 && (
                <div className="warnings-box">
                  <h4>⚠️ Kritik Uyarılar:</h4>
                  <ul>
                    {pdfVerificationResult.uyarilar.map((uyari, index) => (
                      <li key={index}>{uyari}</li>
                    ))}
                  </ul>
                </div>
              )}

              {pdfVerificationResult.imza_bilgisi && (
                <div className="signature-details">
                  <h4>🔏 Dijital İmza Detayları:</h4>
                  <div className="details-grid">
                    <div className="detail-item">
                      <span className="detail-label">İmza Adı:</span>
                      <span className="detail-value">{pdfVerificationResult.imza_bilgisi.imza_adi}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">İmzalayan:</span>
                      <span className="detail-value">{pdfVerificationResult.imza_bilgisi.imzalayan}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">İmza Durumu:</span>
                      <span className={`detail-value ${pdfVerificationResult.imza_bilgisi.gecerli ? 'positive' : 'negative'}`}>
                        {pdfVerificationResult.imza_bilgisi.gecerli ? '✅ Geçerli' : '❌ Geçersiz'}
                      </span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Değiştirilmiş mi?</span>
                      <span className={`detail-value ${pdfVerificationResult.imza_bilgisi.degistirilmis_mi ? 'negative' : 'positive'}`}>
                        {pdfVerificationResult.imza_bilgisi.degistirilmis_mi ? '⚠️ EVET - Değiştirilmiş!' : '✅ Hayır - Orijinal'}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {pdfVerificationResult.hash_dogrulama && (
                <div className="hash-verification">
                  <h4>🔐 Hash Doğrulaması:</h4>
                  <p className={pdfVerificationResult.hash_dogrulama.gecerli ? 'positive' : 'negative'}>
                    {pdfVerificationResult.hash_dogrulama.mesaj}
                  </p>
                </div>
              )}

              {pdfVerificationResult.gecerli && (
                <div className="legal-notice">
                  <h4>⚖️ Hukuki Geçerlilik</h4>
                  <p>
                    Bu PDF belgesi, <strong>pyHanko</strong> dijital imza sistemi ile imzalanmış ve doğrulanmıştır.
                    Belge üzerinde herhangi bir değişiklik yapılmamıştır. <strong>5070 sayılı Elektronik İmza Kanunu</strong> 
                    kapsamında mahkemeye delil olarak sunulabilir.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="help-section">
          <h3>🔒 Güvenlik Notları</h3>
          <ul>
            <li><strong>PDF ile Doğrulama (Önerilen):</strong> PDF dosyasının dijital imzasını pyHanko ile kontrol eder, herhangi bir değişiklik tespit edilir</li>
            <li><strong>SHA-256 Algoritması:</strong> Belgenin dijital parmak izi, tek yönlü hash algoritması ile oluşturulur</li>
            <li><strong>Değiştirilemez:</strong> Belgede tek bir karakter bile değiştirilirse, dijital imza geçersiz olur</li>
            <li><strong>Matematiksel Kesinlik:</strong> Hash çarpışması olasılığı astronomik olarak düşüktür (2^256)</li>
            <li><strong>Database Kaydı:</strong> Tüm mutabakat verileri güvenli SQL Server veritabanında saklanır</li>
            <li><strong>IP Adresi Kaydı:</strong> Her işlem için gerçek ISP IP adresi kaydedilir</li>
          </ul>
        </div>

        <div className="legal-section">
          <h3>⚖️ Yasal Dayanaklar</h3>
          <div className="legal-grid">
            <div className="legal-item">
              <h4>5070 Sayılı Elektronik İmza Kanunu</h4>
              <p>
                <strong>Madde 5:</strong> "Güvenli elektronik imza, elle atılan imza ile aynı hukuki sonucu doğurur."
              </p>
            </div>
            
            <div className="legal-item">
              <h4>6102 Sayılı TTK</h4>
              <p>
                <strong>Madde 18/3:</strong> "Ticari defterler ve belgeler... sicile kayıtlı tacirler arasındaki 
                ticari ilişkilerden doğan davalarında delil teşkil eder."
              </p>
            </div>
            
            <div className="legal-item">
              <h4>6098 Sayılı TBK</h4>
              <p>
                <strong>Madde 88:</strong> "Alacaklı ile borçlu, borç ilişkisinin kapsamı ve içeriği hakkında 
                mutabakata vardıklarında, bu mutabakat sözleşmesi hükmündedir."
              </p>
            </div>
          </div>
        </div>
          </>
        )}
      </div>
    </div>
  )
}

