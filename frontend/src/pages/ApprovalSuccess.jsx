import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FaCheckCircle, FaTimesCircle, FaFileInvoice } from 'react-icons/fa';
import './ApprovalSuccess.css';

function ApprovalSuccess() {
  const location = useLocation();
  const navigate = useNavigate();
  const { message, mutabakat_no, rejected } = location.state || {};

  if (!message) {
    // State yoksa ana sayfaya yönlendir
    window.location.href = '/';
    return null;
  }

  const Icon = rejected ? FaTimesCircle : FaCheckCircle;
  const iconClass = rejected ? 'icon-rejected' : 'icon-approved';

  return (
    <div className="approval-success-container">
      <div className="success-card">
        <Icon className={`success-icon ${iconClass}`} />
        
        <h1>{rejected ? 'Mutabakat Reddedildi' : 'İşlem Başarılı!'}</h1>
        <p className="success-message">{message}</p>

        {mutabakat_no && (
          <div className="mutabakat-info-box">
            <FaFileInvoice className="info-icon" />
            <div>
              <span className="info-label">Mutabakat No:</span>
              <span className="info-value">{mutabakat_no}</span>
            </div>
          </div>
        )}

        <div className="info-text">
          {rejected ? (
            <p>
              Red nedeniniz ilgili şirkete iletilmiştir. <br />
              Gerekirse sizinle iletişime geçilecektir.
            </p>
          ) : (
            <p>
              Mutabakatınız başarıyla onaylanmıştır. <br />
              İlgili şirkete bildirim gönderilmiştir.
            </p>
          )}
        </div>

        <div className="security-notice">
          <p>🔒 Bu link artık kullanılamaz. Bu sayfa kapatılabilir.</p>
        </div>
      </div>
    </div>
  );
}

export default ApprovalSuccess;

