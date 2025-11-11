import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaCheckCircle, FaTimesCircle, FaSpinner, FaFileInvoice, FaCalendarAlt, FaMoneyBillWave, FaShieldAlt } from 'react-icons/fa';
import { toast } from 'react-toastify';
import './PublicApproval.css';

// Üretimde Nginx proxy üzerinden çalışması için relatif /api kullan
const API_URL = '/api';

function PublicApproval() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [mutabakat, setMutabakat] = useState(null);
  const [error, setError] = useState(null);
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [red_nedeni, setRedNedeni] = useState('');
  const [showKVKKConsent, setShowKVKKConsent] = useState(false);
  const [kvkkTexts, setKvkkTexts] = useState(null);
  const [kvkkConsents, setKvkkConsents] = useState({
    kvkk_policy: false,
    customer_notice: false,
    data_retention: false,
    system_consent: false
  });
  const [expandedSections, setExpandedSections] = useState({
    kvkk_policy: false,
    customer_notice: false,
    data_retention: false,
    system_consent: false
  });
  const [submittingKVKK, setSubmittingKVKK] = useState(false);

  useEffect(() => {
    fetchMutabakat();
  }, [token]);

  const fetchMutabakat = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/public/mutabakat/${token}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Mutabakat bulunamadı');
      }

      const data = await response.json();
      setMutabakat(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchKVKKTexts = async () => {
    try {
      const response = await fetch(`${API_URL}/public/mutabakat/${token}/kvkk-texts`);
      if (!response.ok) {
        throw new Error('KVKK metinleri yüklenemedi');
      }
      const data = await response.json();
      setKvkkTexts(data);
    } catch (err) {
      toast.error('KVKK metinleri yüklenemedi');
      console.error(err);
    }
  };

  const handleApprove = async () => {
    if (!window.confirm('Bu mutabakatı onaylamak istediğinizden emin misiniz?')) {
      return;
    }

    try {
      setSubmitting(true);
      const response = await fetch(`${API_URL}/public/mutabakat/${token}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'approve'
        })
      });

      const data = await response.json();

      // KVKK onayı gerekli mi kontrol et
      if (data.requires_kvkk_consent) {
        setShowKVKKConsent(true);
        await fetchKVKKTexts();
        toast.info('Mutabakatı onaylamadan önce KVKK onaylarını tamamlamanız gerekmektedir.');
        setSubmitting(false);
        return;
      }

      if (!response.ok) {
        throw new Error(data.detail || 'Onaylama başarısız');
      }

      toast.success(data.message);
      
      // 3 saniye sonra başarı sayfasına yönlendir
      setTimeout(() => {
        navigate('/mutabakat/onay/basarili', { 
          state: { 
            message: 'Mutabakat başarıyla onaylandı!',
            mutabakat_no: data.mutabakat_no 
          } 
        });
      }, 2000);
    } catch (err) {
      toast.error(err.message);
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleKVKKConsent = async () => {
    const allConsentsGiven = Object.values(kvkkConsents).every(consent => consent === true);
    
    if (!allConsentsGiven) {
      toast.error('Lütfen tüm onayları işaretleyiniz.');
      return;
    }

    try {
      setSubmittingKVKK(true);
      const response = await fetch(`${API_URL}/public/mutabakat/${token}/kvkk-consent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          kvkk_policy_accepted: kvkkConsents.kvkk_policy,
          customer_notice_accepted: kvkkConsents.customer_notice,
          data_retention_accepted: kvkkConsents.data_retention,
          system_consent_accepted: kvkkConsents.system_consent
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'KVKK onayı kaydedilemedi');
      }

      const data = await response.json();
      toast.success(data.message);
      setShowKVKKConsent(false);
      
      // KVKK onaylandıktan sonra tekrar onay dene
      setTimeout(() => {
        handleApprove();
      }, 500);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSubmittingKVKK(false);
    }
  };

  const handleReject = async () => {
    if (!red_nedeni.trim()) {
      toast.error('Lütfen red nedenini belirtiniz');
      return;
    }

    if (!window.confirm('Bu mutabakatı reddetmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      setSubmitting(true);
      const response = await fetch(`${API_URL}/public/mutabakat/${token}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'reject',
          red_nedeni: red_nedeni
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Reddetme başarısız');
      }

      const data = await response.json();
      toast.success(data.message);
      
      // 3 saniye sonra başarı sayfasına yönlendir
      setTimeout(() => {
        navigate('/mutabakat/onay/basarili', { 
          state: { 
            message: 'Mutabakat reddedildi.',
            mutabakat_no: data.mutabakat_no,
            rejected: true 
          } 
        });
      }, 2000);
    } catch (err) {
      toast.error(err.message);
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleConsentChange = (key) => {
    setKvkkConsents(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  if (loading) {
    return (
      <div className="public-approval-container">
        <div className="loading-spinner">
          <FaSpinner className="spinner-icon" />
          <p>Mutabakat yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="public-approval-container">
        <div className="error-card">
          <FaTimesCircle className="error-icon" />
          <h2>Hata</h2>
          <p>{error}</p>
          <p className="error-hint">Bu link geçersiz, kullanılmış veya süresi dolmuş olabilir.</p>
        </div>
      </div>
    );
  }

  if (!mutabakat) {
    return null;
  }

  // KVKK onay sayfası
  if (showKVKKConsent) {
    const allConsentsGiven = Object.values(kvkkConsents).every(consent => consent === true);
    
    return (
      <div className="public-approval-container">
        <div className="public-approval-card kvkk-consent-card">
          <div className="company-header">
            <FaShieldAlt className="kvkk-icon" />
            <h1>🔒 Kişisel Verilerin Korunması (KVKK)</h1>
            <p>Mutabakatı onaylamadan önce KVKK onaylarını tamamlamanız gerekmektedir.</p>
          </div>

          {kvkkTexts ? (
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
                      <h3>{kvkkTexts.kvkk_policy.title}</h3>
                      <p className="kvkk-summary">{kvkkTexts.kvkk_policy.summary}</p>
                    </div>
                    <span className="kvkk-expand-icon">{expandedSections.kvkk_policy ? '−' : '+'}</span>
                  </button>
                </div>
                {expandedSections.kvkk_policy && (
                  <div className="kvkk-content">
                    <pre>{kvkkTexts.kvkk_policy.content}</pre>
                  </div>
                )}
                <label className="kvkk-checkbox">
                  <input
                    type="checkbox"
                    checked={kvkkConsents.kvkk_policy}
                    onChange={() => handleConsentChange('kvkk_policy')}
                  />
                  <span>Okudum, anladım ve kabul ediyorum</span>
                  {kvkkConsents.kvkk_policy && <span className="checkmark">✓</span>}
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
                      <h3>{kvkkTexts.customer_notice.title}</h3>
                      <p className="kvkk-summary">{kvkkTexts.customer_notice.summary}</p>
                    </div>
                    <span className="kvkk-expand-icon">{expandedSections.customer_notice ? '−' : '+'}</span>
                  </button>
                </div>
                {expandedSections.customer_notice && (
                  <div className="kvkk-content">
                    <pre>{kvkkTexts.customer_notice.content}</pre>
                  </div>
                )}
                <label className="kvkk-checkbox">
                  <input
                    type="checkbox"
                    checked={kvkkConsents.customer_notice}
                    onChange={() => handleConsentChange('customer_notice')}
                  />
                  <span>Okudum, anladım ve kabul ediyorum</span>
                  {kvkkConsents.customer_notice && <span className="checkmark">✓</span>}
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
                      <h3>{kvkkTexts.data_retention.title}</h3>
                      <p className="kvkk-summary">{kvkkTexts.data_retention.summary}</p>
                    </div>
                    <span className="kvkk-expand-icon">{expandedSections.data_retention ? '−' : '+'}</span>
                  </button>
                </div>
                {expandedSections.data_retention && (
                  <div className="kvkk-content">
                    <pre>{kvkkTexts.data_retention.content}</pre>
                  </div>
                )}
                <label className="kvkk-checkbox">
                  <input
                    type="checkbox"
                    checked={kvkkConsents.data_retention}
                    onChange={() => handleConsentChange('data_retention')}
                  />
                  <span>Okudum, anladım ve kabul ediyorum</span>
                  {kvkkConsents.data_retention && <span className="checkmark">✓</span>}
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
                      <h3>{kvkkTexts.system_consent.title} ⚠️</h3>
                      <p className="kvkk-summary">{kvkkTexts.system_consent.summary}</p>
                    </div>
                    <span className="kvkk-expand-icon">{expandedSections.system_consent ? '−' : '+'}</span>
                  </button>
                </div>
                {expandedSections.system_consent && (
                  <div className="kvkk-content">
                    <pre>{kvkkTexts.system_consent.content}</pre>
                  </div>
                )}
                <label className="kvkk-checkbox">
                  <input
                    type="checkbox"
                    checked={kvkkConsents.system_consent}
                    onChange={() => handleConsentChange('system_consent')}
                  />
                  <span>Okudum, anladım ve kabul ediyorum (Zorunlu)</span>
                  {kvkkConsents.system_consent && <span className="checkmark">✓</span>}
                </label>
              </div>
            </div>
          ) : (
            <div className="loading-spinner">
              <FaSpinner className="spinner-icon" />
              <p>KVKK metinleri yükleniyor...</p>
            </div>
          )}

          <div className="kvkk-footer">
            <button
              onClick={handleKVKKConsent}
              disabled={!allConsentsGiven || submittingKVKK}
              className={`btn btn-primary btn-large ${!allConsentsGiven ? 'btn-disabled' : ''}`}
            >
              {submittingKVKK ? (
                <>
                  <FaSpinner className="spinner-icon" />
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
    );
  }

  // Normal mutabakat onay sayfası
  return (
    <div className="public-approval-container">
      <div className="public-approval-card">
        <div className="company-header">
          <h1>Dino Gıda - E-Mutabakat</h1>
          <p>Mutabakat Onay Sayfası</p>
        </div>

        <div className="mutabakat-info">
          <h2><FaFileInvoice /> Mutabakat Detayları</h2>
          
          <div className="info-row">
            <span className="info-label">Mutabakat No:</span>
            <span className="info-value">{mutabakat.mutabakat_no}</span>
          </div>

          <div className="info-row">
            <span className="info-label"><FaCalendarAlt /> Dönem:</span>
            <span className="info-value">
              {new Date(mutabakat.donem_baslangic).toLocaleDateString('tr-TR')} - {new Date(mutabakat.donem_bitis).toLocaleDateString('tr-TR')}
            </span>
          </div>

          <div className="info-row">
            <span className="info-label"><FaMoneyBillWave /> Toplam Borç:</span>
            <span className="info-value money">{mutabakat.toplam_borc?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} TL</span>
          </div>

          <div className="info-row">
            <span className="info-label"><FaMoneyBillWave /> Toplam Alacak:</span>
            <span className="info-value money">{mutabakat.toplam_alacak?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} TL</span>
          </div>

          <div className="info-row balance">
            <span className="info-label"><FaMoneyBillWave /> Bakiye:</span>
            <span className={`info-value money ${mutabakat.bakiye < 0 ? 'negative' : 'positive'}`}>
              {mutabakat.bakiye?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} TL
            </span>
          </div>

          {mutabakat.aciklama && (
            <div className="info-row full-width">
              <span className="info-label">Açıklama:</span>
              <p className="info-text">{mutabakat.aciklama}</p>
            </div>
          )}
        </div>

        {!showRejectForm ? (
          <div className="action-buttons">
            <button 
              className="btn btn-approve" 
              onClick={handleApprove}
              disabled={submitting}
            >
              {submitting ? (
                <><FaSpinner className="spinner-icon" /> İşleniyor...</>
              ) : (
                <><FaCheckCircle /> Onayla</>
              )}
            </button>
            <button 
              className="btn btn-reject" 
              onClick={() => setShowRejectForm(true)}
              disabled={submitting}
            >
              <FaTimesCircle /> Reddet
            </button>
          </div>
        ) : (
          <div className="reject-form">
            <h3>Red Nedeni</h3>
            <textarea
              value={red_nedeni}
              onChange={(e) => setRedNedeni(e.target.value)}
              placeholder="Lütfen mutabakatı reddetme nedeninizi belirtiniz..."
              rows="4"
              disabled={submitting}
            />
            <div className="reject-form-buttons">
              <button 
                className="btn btn-reject-confirm" 
                onClick={handleReject}
                disabled={submitting || !red_nedeni.trim()}
              >
                {submitting ? (
                  <><FaSpinner className="spinner-icon" /> İşleniyor...</>
                ) : (
                  <><FaTimesCircle /> Reddet</>
                )}
              </button>
              <button 
                className="btn btn-cancel" 
                onClick={() => {
                  setShowRejectForm(false);
                  setRedNedeni('');
                }}
                disabled={submitting}
              >
                İptal
              </button>
            </div>
          </div>
        )}

        <div className="security-notice">
          <p>🔒 Bu link tek kullanımlıktır. Onaylama veya reddetme işleminden sonra tekrar kullanılamaz.</p>
        </div>
      </div>
    </div>
  );
}

export default PublicApproval;
