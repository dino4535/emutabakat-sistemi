import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaCheckCircle, FaTimesCircle, FaSpinner, FaFileInvoice, FaCalendarAlt, FaMoneyBillWave } from 'react-icons/fa';
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

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Onaylama başarısız');
      }

      const data = await response.json();
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
      const response = await fetch(`${API_URL}/api/public/mutabakat/${token}/action`, {
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

