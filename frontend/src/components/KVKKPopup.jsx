import { useState, useEffect } from 'react'
import axios from 'axios'
import './KVKKPopup.css'

export default function KVKKPopup({ onComplete }) {
  const [texts, setTexts] = useState(null)
  const [loading, setLoading] = useState(true)
  const [consents, setConsents] = useState({
    kvkk_policy: false,
    customer_notice: false,
    data_retention: false,
    system_consent: false
  })
  // Başlangıçta tüm bölümler kapalı
  const [expandedSections, setExpandedSections] = useState({
    kvkk_policy: false,
    customer_notice: false,
    data_retention: false,
    system_consent: false
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchKVKKTexts()
  }, [])

  const fetchKVKKTexts = async () => {
    try {
      const response = await axios.get('/api/kvkk/texts')
      setTexts(response.data)
      setLoading(false)
    } catch (err) {
      console.error('KVKK metinleri yüklenemedi:', err)
      setError('KVKK metinleri yüklenemedi. Lütfen sayfayı yenileyin.')
      setLoading(false)
    }
  }

  const handleConsentChange = (key) => {
    setConsents(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const allConsentsGiven = Object.values(consents).every(consent => consent === true)

  const handleSubmit = async () => {
    if (!allConsentsGiven) {
      setError('Lütfen tüm onayları işaretleyiniz.')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      await axios.post('/api/kvkk/consent', {
        kvkk_policy_accepted: consents.kvkk_policy,
        customer_notice_accepted: consents.customer_notice,
        data_retention_accepted: consents.data_retention,
        system_consent_accepted: consents.system_consent
      })

      // Başarılı, popup'ı kapat
      onComplete()
    } catch (err) {
      console.error('KVKK onayı kaydedilemedi:', err)
      setError(err.response?.data?.detail || 'Bir hata oluştu. Lütfen tekrar deneyin.')
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="kvkk-popup-overlay">
        <div className="kvkk-popup">
          <div className="kvkk-loading">
            <div className="spinner"></div>
            <p>KVKK metinleri yükleniyor...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error && !texts) {
    return (
      <div className="kvkk-popup-overlay">
        <div className="kvkk-popup">
          <div className="kvkk-error">
            <p>{error}</p>
            <button onClick={fetchKVKKTexts} className="btn btn-primary">
              Tekrar Dene
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="kvkk-popup-overlay">
      <div className="kvkk-popup">
        <div className="kvkk-header">
          <h2>🔒 Kişisel Verilerin Korunması (KVKK)</h2>
          <p className="kvkk-description">
            Sistemimizi kullanmaya başlamadan önce, lütfen aşağıdaki metinleri okuyup onaylayınız.
            Onaylarınız tarih, saat ve IP bilgisi ile birlikte yasal delil olarak kaydedilecektir.
          </p>
        </div>

        <div className="kvkk-sections">
          {/* 1. KVKK Politikası */}
          <div className="kvkk-section">
            <div className="kvkk-section-header">
              <button 
                className={`kvkk-expand-btn ${expandedSections.kvkk_policy ? 'expanded' : ''}`}
                onClick={() => toggleSection('kvkk_policy')}
              >
                <span className="kvkk-number">1</span>
                <div className="kvkk-title-area">
                  <h3>{texts?.kvkk_policy?.title}</h3>
                  <p className="kvkk-summary">{texts?.kvkk_policy?.summary}</p>
                </div>
                <span className="kvkk-expand-icon">{expandedSections.kvkk_policy ? '−' : '+'}</span>
              </button>
            </div>
            {expandedSections.kvkk_policy && (
              <div className="kvkk-content">
                <pre>{texts?.kvkk_policy?.content}</pre>
              </div>
            )}
            <label className="kvkk-checkbox">
              <input
                type="checkbox"
                checked={consents.kvkk_policy}
                onChange={() => handleConsentChange('kvkk_policy')}
              />
              <span>Okudum, anladım ve kabul ediyorum</span>
              {consents.kvkk_policy && <span className="checkmark">✓</span>}
            </label>
          </div>

          {/* 2. Müşteri Aydınlatma Metni */}
          <div className="kvkk-section">
            <div className="kvkk-section-header">
              <button 
                className={`kvkk-expand-btn ${expandedSections.customer_notice ? 'expanded' : ''}`}
                onClick={() => toggleSection('customer_notice')}
              >
                <span className="kvkk-number">2</span>
                <div className="kvkk-title-area">
                  <h3>{texts?.customer_notice?.title}</h3>
                  <p className="kvkk-summary">{texts?.customer_notice?.summary}</p>
                </div>
                <span className="kvkk-expand-icon">{expandedSections.customer_notice ? '−' : '+'}</span>
              </button>
            </div>
            {expandedSections.customer_notice && (
              <div className="kvkk-content">
                <pre>{texts?.customer_notice?.content}</pre>
              </div>
            )}
            <label className="kvkk-checkbox">
              <input
                type="checkbox"
                checked={consents.customer_notice}
                onChange={() => handleConsentChange('customer_notice')}
              />
              <span>Okudum, anladım ve kabul ediyorum</span>
              {consents.customer_notice && <span className="checkmark">✓</span>}
            </label>
          </div>

          {/* 3. Kişisel Veri Saklama ve İmha Politikası */}
          <div className="kvkk-section">
            <div className="kvkk-section-header">
              <button 
                className={`kvkk-expand-btn ${expandedSections.data_retention ? 'expanded' : ''}`}
                onClick={() => toggleSection('data_retention')}
              >
                <span className="kvkk-number">3</span>
                <div className="kvkk-title-area">
                  <h3>{texts?.data_retention?.title}</h3>
                  <p className="kvkk-summary">{texts?.data_retention?.summary}</p>
                </div>
                <span className="kvkk-expand-icon">{expandedSections.data_retention ? '−' : '+'}</span>
              </button>
            </div>
            {expandedSections.data_retention && (
              <div className="kvkk-content">
                <pre>{texts?.data_retention?.content}</pre>
              </div>
            )}
            <label className="kvkk-checkbox">
              <input
                type="checkbox"
                checked={consents.data_retention}
                onChange={() => handleConsentChange('data_retention')}
              />
              <span>Okudum, anladım ve kabul ediyorum</span>
              {consents.data_retention && <span className="checkmark">✓</span>}
            </label>
          </div>

          {/* 4. E-Mutabakat Sistemi Kullanım Onayı */}
          <div className="kvkk-section kvkk-section-highlighted">
            <div className="kvkk-section-header">
              <button 
                className={`kvkk-expand-btn ${expandedSections.system_consent ? 'expanded' : ''}`}
                onClick={() => toggleSection('system_consent')}
              >
                <span className="kvkk-number">4</span>
                <div className="kvkk-title-area">
                  <h3>{texts?.system_consent?.title} ⚠️</h3>
                  <p className="kvkk-summary">{texts?.system_consent?.summary}</p>
                </div>
                <span className="kvkk-expand-icon">{expandedSections.system_consent ? '−' : '+'}</span>
              </button>
            </div>
            {expandedSections.system_consent && (
              <div className="kvkk-content">
                <pre>{texts?.system_consent?.content}</pre>
              </div>
            )}
            <label className="kvkk-checkbox">
              <input
                type="checkbox"
                checked={consents.system_consent}
                onChange={() => handleConsentChange('system_consent')}
              />
              <span>Okudum, anladım ve kabul ediyorum (Zorunlu)</span>
              {consents.system_consent && <span className="checkmark">✓</span>}
            </label>
          </div>
        </div>

        {error && (
          <div className="kvkk-alert kvkk-alert-error">
            {error}
          </div>
        )}

        <div className="kvkk-footer">
          <div className="kvkk-info-box">
            <p>
              <strong>📌 ÖNEMLİ BİLGİLENDİRME:</strong>
            </p>
            <ul>
              <li>Onaylarınız <strong>tarih, IP ve ISP bilgisi</strong> ile kaydedilir.</li>
              <li>Kayıtlar <strong>10 yıl</strong> yasal delil olarak saklanır.</li>
              <li>Tüm onaylar zorunludur.</li>
            </ul>
            
            <div className="kvkk-links-section">
              <p><strong>📄 Detaylı bilgi için:</strong></p>
              <div className="kvkk-links">
                <a href="https://dinogida.com.tr/kvkk/" target="_blank" rel="noopener noreferrer">
                  <span className="link-icon">🔗</span>
                  <span className="link-text">KVKK Politikası</span>
                </a>
                <a href="https://dinogida.com.tr/musteri-aydinlatma-metni/" target="_blank" rel="noopener noreferrer">
                  <span className="link-icon">🔗</span>
                  <span className="link-text">Müşteri Aydınlatma Metni</span>
                </a>
                <a href="https://dinogida.com.tr/kisisel-veri-saklama-ve-imha-politikasi/" target="_blank" rel="noopener noreferrer">
                  <span className="link-icon">🔗</span>
                  <span className="link-text">Kişisel Veri Saklama ve İmha</span>
                </a>
              </div>
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={!allConsentsGiven || submitting}
            className={`btn btn-primary btn-large ${!allConsentsGiven ? 'btn-disabled' : ''}`}
          >
            {submitting ? (
              <>
                <span className="spinner-small"></span>
                Kaydediliyor...
              </>
            ) : (
              <>
                {allConsentsGiven ? '✓' : '⚠️'} Tüm Onayları Kaydet ve Devam Et
              </>
            )}
          </button>

          {!allConsentsGiven && (
            <p className="kvkk-warning">
              ⚠️ Lütfen devam edebilmek için tüm metinleri okuyup onaylayınız.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

