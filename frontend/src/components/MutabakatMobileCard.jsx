import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { tr } from 'date-fns/locale';
import { FaEye, FaPaperPlane, FaFilePdf } from 'react-icons/fa';
import LoadingButton from './LoadingButton';

/**
 * Mutabakat Mobile Card Component
 * Mobil cihazlarda tablo yerine card görünümü
 */
const MutabakatMobileCard = ({ 
  mutabakat, 
  isCustomer, 
  isReceiver,
  isSender,
  sendingId,
  onSend,
  onPreviewPDF,
  formatCurrency,
  getDurumBadge,
  getDurumText
}) => {
  return (
    <div className={`mutabakat-card ${isCustomer && mutabakat.durum === 'gonderildi' && isReceiver ? 'highlight' : ''}`}>
      {/* Header */}
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-mutabakat-no">{mutabakat.mutabakat_no}</div>
          <div className="card-date">
            {format(new Date(mutabakat.created_at), 'dd MMM yyyy', { locale: tr })}
          </div>
        </div>
        <div className="card-status">
          <span className={`badge ${getDurumBadge(mutabakat.durum)}`}>
            {getDurumText(mutabakat.durum)}
            {isCustomer && mutabakat.durum === 'gonderildi' && isReceiver && ' ⏳'}
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="card-body">
        {/* Gönderen/Alıcı */}
        {!isCustomer && (
          <div className="card-field">
            <div className="card-field-label">
              {isSender ? 'Alıcı' : 'Gönderen'}
            </div>
            <div className="card-field-value">
              {isSender 
                ? (mutabakat.receiver?.company_name || mutabakat.receiver?.full_name)
                : (mutabakat.sender?.company_name || mutabakat.sender?.full_name)
              }
            </div>
          </div>
        )}

        {isCustomer && (
          <div className="card-field">
            <div className="card-field-label">Gönderen</div>
            <div className="card-field-value">
              {mutabakat.sender?.company_name || mutabakat.sender?.full_name || 'Dino Gıda'}
            </div>
          </div>
        )}

        {/* Dönem */}
        <div className="card-field">
          <div className="card-field-label">Dönem</div>
          <div className="card-field-value">
            {format(new Date(mutabakat.donem_baslangic), 'dd MMM', { locale: tr })} - {format(new Date(mutabakat.donem_bitis), 'dd MMM yyyy', { locale: tr })}
          </div>
        </div>

        {/* Borç */}
        <div className="card-field">
          <div className="card-field-label">Borç</div>
          <div className="card-field-value borc">
            {formatCurrency(mutabakat.toplam_borc)}
          </div>
        </div>

        {/* Alacak */}
        <div className="card-field">
          <div className="card-field-label">Alacak</div>
          <div className="card-field-value alacak">
            {formatCurrency(mutabakat.toplam_alacak)}
          </div>
        </div>

        {/* Bakiye */}
        <div className="card-field">
          <div className="card-field-label">Bakiye</div>
          <div className={`card-field-value ${mutabakat.bakiye >= 0 ? 'alacak' : 'borc'}`}>
            {formatCurrency(mutabakat.bakiye)}
          </div>
        </div>

        {/* Bayi Sayısı */}
        {mutabakat.toplam_bayi_sayisi > 0 && (
          <div className="card-field">
            <div className="card-field-label">Bayi</div>
            <div className="card-field-value">
              {mutabakat.toplam_bayi_sayisi} adet
            </div>
          </div>
        )}
      </div>

      {/* Footer - İşlem Butonları */}
      <div className="card-footer">
        <Link to={`/mutabakat/${mutabakat.id}`} className="btn btn-sm btn-outline">
          <FaEye /> {isCustomer && mutabakat.durum === 'gonderildi' && isReceiver ? 'İncele & Onayla' : 'Görüntüle'}
        </Link>

        {(mutabakat.durum === 'onaylandi' || mutabakat.durum === 'reddedildi') && onPreviewPDF && (
          <button
            onClick={() => onPreviewPDF(mutabakat)}
            className="btn btn-sm btn-info"
          >
            <FaFilePdf /> Önizle
          </button>
        )}

        {mutabakat.durum === 'taslak' && !isCustomer && onSend && (
          <LoadingButton
            onClick={() => onSend(mutabakat.id, mutabakat.mutabakat_no)}
            loading={sendingId === mutabakat.id}
            size="small"
            variant="success"
            icon={<FaPaperPlane />}
            loadingText="Gönderiliyor..."
          >
            Gönder
          </LoadingButton>
        )}
      </div>
    </div>
  );
};

export default MutabakatMobileCard;

