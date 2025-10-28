import React, { useState, useEffect } from 'react';
import './PDFPreviewModal.css';

const PDFPreviewModal = ({ isOpen, onClose, pdfUrl, fileName = 'document.pdf' }) => {
  const [scale, setScale] = useState(100);

  // Zoom fonksiyonları
  const zoomIn = () => {
    setScale(prev => Math.min(prev + 25, 200));
  };

  const zoomOut = () => {
    setScale(prev => Math.max(prev - 25, 50));
  };

  const resetZoom = () => {
    setScale(100);
  };

  // Print fonksiyonu
  const handlePrint = () => {
    const iframe = document.getElementById('pdf-iframe');
    if (iframe) {
      iframe.contentWindow.print();
    }
  };

  // Download fonksiyonu
  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = fileName;
    link.click();
  };

  // Modal kapatma (ESC tuşu)
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Modal açık değilse render etme
  if (!isOpen) return null;

  return (
    <div className="pdf-preview-modal-overlay" onClick={onClose}>
      <div className="pdf-preview-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="pdf-preview-header">
          <div className="pdf-preview-title">
            <i className="fas fa-file-pdf"></i>
            <span>{fileName}</span>
          </div>
          <button className="pdf-close-btn" onClick={onClose}>
            <i className="fas fa-times"></i>
          </button>
        </div>

        {/* Toolbar */}
        <div className="pdf-preview-toolbar">
          {/* Zoom Controls */}
          <div className="toolbar-group">
            <button 
              className="toolbar-btn" 
              onClick={zoomOut}
              disabled={scale <= 50}
              title="Uzaklaştır"
            >
              <i className="fas fa-search-minus"></i>
            </button>
            <span className="zoom-level">{scale}%</span>
            <button 
              className="toolbar-btn" 
              onClick={zoomIn}
              disabled={scale >= 200}
              title="Yakınlaştır"
            >
              <i className="fas fa-search-plus"></i>
            </button>
            <button 
              className="toolbar-btn" 
              onClick={resetZoom}
              title="Orijinal Boyut"
            >
              <i className="fas fa-expand-arrows-alt"></i>
            </button>
          </div>

          {/* Actions */}
          <div className="toolbar-group">
            <button 
              className="toolbar-btn" 
              onClick={handlePrint}
              title="Yazdır"
            >
              <i className="fas fa-print"></i>
            </button>
            <button 
              className="toolbar-btn" 
              onClick={handleDownload}
              title="İndir"
            >
              <i className="fas fa-download"></i>
            </button>
          </div>
        </div>

        {/* PDF Viewer - iframe kullanarak */}
        <div className="pdf-preview-content">
          <iframe
            id="pdf-iframe"
            src={`${pdfUrl}#zoom=${scale}`}
            title={fileName}
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
              background: '#525659'
            }}
          />
        </div>

        {/* Footer Info */}
        <div className="pdf-preview-footer">
          <span>
            <i className="fas fa-info-circle"></i>
            {fileName} • Dijital İmzalı Mutabakat Belgesi
          </span>
        </div>
      </div>
    </div>
  );
};

export default PDFPreviewModal;
