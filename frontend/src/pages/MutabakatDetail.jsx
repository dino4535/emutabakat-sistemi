import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'
import { format } from 'date-fns'
import { tr } from 'date-fns/locale'
import { toast } from 'react-toastify'
import { FaArrowLeft, FaCheckCircle, FaTimesCircle, FaPaperPlane, FaTrash, FaFilePdf, FaEye } from 'react-icons/fa'
import { useState } from 'react'
import PDFPreviewModal from '../components/PDFPreviewModal'
import './MutabakatDetail.css'

export default function MutabakatDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user: current_user } = useAuth()
  const [redNedeni, setRedNedeni] = useState('')
  const [ekstreTalepEt, setEkstreTalepEt] = useState(false)
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [showPDFPreview, setShowPDFPreview] = useState(false)
  const [pdfUrl, setPdfUrl] = useState(null)

  const { data: mutabakat, isLoading } = useQuery({
    queryKey: ['mutabakat', id],
    queryFn: async () => {
      const response = await axios.get(`/api/mutabakat/${id}`)
      return response.data
    }
  })

  const sendMutation = useMutation({
    mutationFn: async () => {
      await axios.post(`/api/mutabakat/${id}/send`)
    },
    onSuccess: () => {
      toast.success('Mutabakat gönderildi!')
      queryClient.invalidateQueries(['mutabakat', id])
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Mutabakat gönderilemedi')
    }
  })

  const approveMutation = useMutation({
    mutationFn: async () => {
      await axios.post(`/api/mutabakat/${id}/approve`)
    },
    onSuccess: () => {
      toast.success('Mutabakat onaylandı!')
      queryClient.invalidateQueries(['mutabakat', id])
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Mutabakat onaylanamadı')
    }
  })

  const rejectMutation = useMutation({
    mutationFn: async ({ red_nedeni, ekstre_talep_edildi }) => {
      await axios.post(`/api/mutabakat/${id}/reject?red_nedeni=${encodeURIComponent(red_nedeni)}&ekstre_talep_edildi=${ekstre_talep_edildi}`)
    },
    onSuccess: () => {
      toast.success(ekstreTalepEt ? 'Mutabakat reddedildi. Detaylı ekstre talebi kaydedildi.' : 'Mutabakat reddedildi')
      setShowRejectModal(false)
      setRedNedeni('')
      setEkstreTalepEt(false)
      queryClient.invalidateQueries(['mutabakat', id])
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Mutabakat reddedilemedi')
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async () => {
      await axios.delete(`/api/mutabakat/${id}`)
    },
    onSuccess: () => {
      toast.success('Mutabakat silindi')
      navigate('/mutabakat')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Mutabakat silinemedi')
    }
  })

  const handleReject = () => {
    if (!redNedeni.trim()) {
      toast.error('Lütfen red nedeni girin')
      return
    }
    rejectMutation.mutate({ 
      red_nedeni: redNedeni,
      ekstre_talep_edildi: ekstreTalepEt 
    })
  }

  const handlePreviewPDF = async () => {
    try {
      const response = await axios.get(`/api/mutabakat/${id}/download-pdf`, {
        responseType: 'blob'
      })
      
      // Blob'dan URL oluştur
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      setPdfUrl(url)
      setShowPDFPreview(true)
    } catch (error) {
      toast.error('PDF yüklenemedi: ' + (error.response?.data?.detail || 'Bilinmeyen hata'))
    }
  }

  const handleDownloadPDF = async () => {
    try {
      const response = await axios.get(`/api/mutabakat/${id}/download-pdf`, {
        responseType: 'blob' // PDF binary data
      })
      
      // Blob'dan URL oluştur
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      
      // Link oluştur ve tıkla
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `Mutabakat_${mutabakat.mutabakat_no}.pdf`)
      document.body.appendChild(link)
      link.click()
      
      // Temizle
      link.parentNode.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast.success('PDF indiriliyor...')
    } catch (error) {
      toast.error('PDF indirilemedi: ' + (error.response?.data?.detail || 'Bilinmeyen hata'))
    }
  }

  if (isLoading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  if (!mutabakat) {
    return <div>Mutabakat bulunamadı</div>
  }

  const getDurumBadge = (durum) => {
    const badges = {
      taslak: 'badge-secondary',
      gonderildi: 'badge-warning',
      onaylandi: 'badge-success',
      reddedildi: 'badge-danger'
    }
    return badges[durum] || 'badge-secondary'
  }

  const getDurumText = (durum) => {
    const texts = {
      taslak: 'Taslak',
      gonderildi: 'Gönderildi',
      onaylandi: 'Onaylandı',
      reddedildi: 'Reddedildi'
    }
    return texts[durum] || durum
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY'
    }).format(amount || 0)
  }

  // Yetki kontrolleri
  const isSender = mutabakat.sender_id === current_user?.id
  const isReceiver = mutabakat.receiver_id === current_user?.id
  const isCustomer = ['musteri', 'MUSTERI', 'tedarikci', 'TEDARIKCI'].includes(current_user?.role)
  const canCreateMutabakat = ['admin', 'muhasebe', 'planlama', 'ADMIN', 'MUHASEBE', 'PLANLAMA'].includes(current_user?.role)
  
  // Buton yetkileri
  const canSend = isSender && mutabakat.durum === 'taslak' && canCreateMutabakat
  const canApprove = isReceiver && mutabakat.durum === 'gonderildi'
  const canReject = isReceiver && mutabakat.durum === 'gonderildi'
  const canDelete = isSender && mutabakat.durum === 'taslak' && canCreateMutabakat
  
  // Debug için console.log ekle
  console.log('User:', current_user)
  console.log('Mutabakat:', { sender_id: mutabakat.sender_id, receiver_id: mutabakat.receiver_id, durum: mutabakat.durum })
  console.log('Yetkiler:', { isSender, isReceiver, isCustomer, canApprove, canReject })

  return (
    <div className="mutabakat-detail">
      <div className="detail-header">
        <button onClick={() => navigate('/mutabakat')} className="btn btn-outline">
          <FaArrowLeft /> Geri
        </button>
        <div className="header-actions">
          {canSend && (
            <button
              onClick={() => sendMutation.mutate()}
              className="btn btn-primary"
              disabled={sendMutation.isPending}
            >
              <FaPaperPlane /> Gönder
            </button>
          )}
          {canApprove && (
            <button
              onClick={() => approveMutation.mutate()}
              className="btn btn-success"
              disabled={approveMutation.isPending}
            >
              <FaCheckCircle /> Onayla
            </button>
          )}
          {canReject && (
            <button
              onClick={() => setShowRejectModal(true)}
              className="btn btn-danger"
            >
              <FaTimesCircle /> Reddet
            </button>
          )}
          {/* PDF İndirme ve Önizleme Butonları - Onaylanan veya Reddedilen mutabakatlar için */}
          {(mutabakat.durum === 'onaylandi' || mutabakat.durum === 'reddedildi') && (
            <>
              <button
                onClick={handlePreviewPDF}
                className="btn btn-secondary"
                title="PDF Önizleme - İndirmeden Görüntüle"
              >
                <FaEye /> PDF Önizle
              </button>
              <button
                onClick={handleDownloadPDF}
                className="btn btn-info"
                title="Resmi Mutabakat Belgesini İndir (Dijital İmzalı)"
              >
                <FaFilePdf /> PDF İndir
              </button>
            </>
          )}
          {canDelete && (
            <button
              onClick={() => {
                if (window.confirm('Mutabakatı silmek istediğinizden emin misiniz?')) {
                  deleteMutation.mutate()
                }
              }}
              className="btn btn-danger"
              disabled={deleteMutation.isPending}
            >
              <FaTrash /> Sil
            </button>
          )}
        </div>
      </div>

      <div className="detail-content">
        <div className="card">
          <div className="info-header">
            <div>
              <h2>{mutabakat.mutabakat_no}</h2>
              <p className="text-secondary">
                Oluşturulma: {format(new Date(mutabakat.created_at), 'dd MMMM yyyy HH:mm', { locale: tr })}
              </p>
            </div>
            <span className={`badge badge-lg ${getDurumBadge(mutabakat.durum)}`}>
              {getDurumText(mutabakat.durum)}
            </span>
          </div>

          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Gönderen:</span>
              <span className="info-value">{mutabakat.sender?.company_name || mutabakat.sender?.full_name}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Alıcı:</span>
              <span className="info-value">{mutabakat.receiver?.company_name || mutabakat.receiver?.full_name}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Dönem Başlangıç:</span>
              <span className="info-value">
                {format(new Date(mutabakat.donem_baslangic), 'dd MMMM yyyy', { locale: tr })}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Dönem Bitiş:</span>
              <span className="info-value">
                {format(new Date(mutabakat.donem_bitis), 'dd MMMM yyyy', { locale: tr })}
              </span>
            </div>
          </div>

          {mutabakat.aciklama && (
            <div className="info-section">
              <span className="info-label">Açıklama:</span>
              <p className="info-description">{mutabakat.aciklama}</p>
            </div>
          )}

          {mutabakat.red_nedeni && (
            <div className="info-section red-section">
              <span className="info-label">Red Nedeni:</span>
              <p className="info-description">{mutabakat.red_nedeni}</p>
            </div>
          )}
        </div>

        <div className="card totals-card">
          <h3>Özet</h3>
          <div className="totals-list">
            <div className="total-row">
              <span>Toplam Borç:</span>
              <span className="text-danger">{formatCurrency(mutabakat.toplam_borc)}</span>
            </div>
            <div className="total-row">
              <span>Toplam Alacak:</span>
              <span className="text-success">{formatCurrency(mutabakat.toplam_alacak)}</span>
            </div>
            <div className="total-row total-final">
              <span>Bakiye:</span>
              <span className={mutabakat.bakiye >= 0 ? 'text-success' : 'text-danger'}>
                {formatCurrency(mutabakat.bakiye)}
              </span>
            </div>
          </div>
        </div>

        {/* Bayi Detayları */}
        {mutabakat.bayi_detaylari && mutabakat.bayi_detaylari.length > 0 && (
          <div className="card">
            <h3>🏪 Bayi Detayları ({mutabakat.bayi_detaylari.length} Bayi)</h3>
            <div className="table-responsive">
              <table className="detail-table">
                <thead>
                  <tr>
                    <th>Bayi Kodu</th>
                    <th>Bayi Adı</th>
                    <th className="text-right">Bakiye</th>
                  </tr>
                </thead>
                <tbody>
                  {mutabakat.bayi_detaylari.map((bayi, index) => (
                    <tr key={index}>
                      <td>{bayi.bayi_kodu}</td>
                      <td>{bayi.bayi_adi}</td>
                      <td className={`text-right ${bayi.bakiye > 0 ? 'text-success' : bayi.bakiye < 0 ? 'text-danger' : ''}`}>
                        {formatCurrency(bayi.bakiye)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="total-row">
                    <td colSpan="2"><strong>TOPLAM</strong></td>
                    <td className={`text-right ${mutabakat.bakiye > 0 ? 'text-success' : mutabakat.bakiye < 0 ? 'text-danger' : ''}`}>
                      <strong>{formatCurrency(mutabakat.bakiye)}</strong>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Red Modal */}
      {showRejectModal && (
        <div className="modal-overlay" onClick={() => setShowRejectModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Mutabakat Reddetme</h3>
            <div className="form-group">
              <label className="form-label">Red Nedeni *</label>
              <textarea
                className="form-textarea"
                value={redNedeni}
                onChange={(e) => setRedNedeni(e.target.value)}
                placeholder="Lütfen red nedeninizi açıklayın..."
                rows="4"
              />
            </div>
            
            <div className="form-group checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={ekstreTalepEt}
                  onChange={(e) => setEkstreTalepEt(e.target.checked)}
                />
                <span className="checkbox-text">
                  📄 <strong>Detaylı cari ekstre talep ediyorum</strong>
                </span>
              </label>
            </div>
            
            <div className="modal-actions">
              <button
                onClick={() => setShowRejectModal(false)}
                className="btn btn-secondary"
              >
                İptal
              </button>
              <button
                onClick={handleReject}
                className="btn btn-danger"
                disabled={rejectMutation.isPending}
              >
                {rejectMutation.isPending ? 'Reddediliyor...' : 'Reddet'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PDF Preview Modal */}
      {pdfUrl && (
        <PDFPreviewModal
          isOpen={showPDFPreview}
          onClose={() => {
            setShowPDFPreview(false)
            // Clean up blob URL
            if (pdfUrl) {
              window.URL.revokeObjectURL(pdfUrl)
              setPdfUrl(null)
            }
          }}
          pdfUrl={pdfUrl}
          fileName={`Mutabakat_${mutabakat?.mutabakat_no || 'Belge'}.pdf`}
        />
      )}
    </div>
  )
}

