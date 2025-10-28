import React from 'react';
import { FaInbox, FaSearch, FaExclamationTriangle, FaPlus } from 'react-icons/fa';
import './EmptyState.css';

/**
 * Empty State Component
 * Boş liste/tablo durumlarında güzel bir görünüm
 * 
 * @param {string} type - 'no-data' | 'no-results' | 'error' | 'no-access'
 * @param {string} title - Başlık
 * @param {string} description - Açıklama
 * @param {React.Node} icon - Custom icon
 * @param {function} action - Action button callback
 * @param {string} actionText - Action button metni
 */
const EmptyState = ({
  type = 'no-data',
  title,
  description,
  icon,
  action,
  actionText = 'Yeni Ekle',
  children
}) => {
  // Default icons
  const defaultIcons = {
    'no-data': <FaInbox />,
    'no-results': <FaSearch />,
    'error': <FaExclamationTriangle />,
    'no-access': <FaExclamationTriangle />
  };
  
  // Default titles
  const defaultTitles = {
    'no-data': 'Henüz veri yok',
    'no-results': 'Sonuç bulunamadı',
    'error': 'Bir hata oluştu',
    'no-access': 'Erişim izniniz yok'
  };
  
  // Default descriptions
  const defaultDescriptions = {
    'no-data': 'İlk kaydı oluşturarak başlayın',
    'no-results': 'Arama kriterlerinizi değiştirip tekrar deneyin',
    'error': 'Bir şeyler ters gitti. Lütfen tekrar deneyin',
    'no-access': 'Bu sayfayı görüntülemek için yetkiniz bulunmuyor'
  };
  
  const displayIcon = icon || defaultIcons[type];
  const displayTitle = title || defaultTitles[type];
  const displayDescription = description || defaultDescriptions[type];
  
  return (
    <div className={`empty-state empty-state-${type} animate-fadeInUp`}>
      <div className="empty-state-icon">
        {displayIcon}
      </div>
      
      <h3 className="empty-state-title">{displayTitle}</h3>
      
      {displayDescription && (
        <p className="empty-state-description">{displayDescription}</p>
      )}
      
      {action && (
        <button
          onClick={action}
          className="empty-state-action btn btn-primary"
        >
          <FaPlus /> {actionText}
        </button>
      )}
      
      {children && (
        <div className="empty-state-custom">
          {children}
        </div>
      )}
    </div>
  );
};

export default EmptyState;

