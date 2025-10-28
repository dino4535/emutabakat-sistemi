import { useState } from 'react'
import axios from 'axios'
import { toast } from 'react-toastify'
import { FaSearch, FaFileAlt, FaPrint, FaDownload, FaUser, FaBuilding, FaShieldAlt, FaExclamationTriangle } from 'react-icons/fa'
import './LegalReports.css'

export default function LegalReports() {
  const [searchTerm, setSearchTerm] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [selectedReport, setSelectedReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [reportLoading, setReportLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    
    if (!searchTerm.trim()) {
      toast.error('Lütfen VKN veya Mutabakat Numarası girin')
      return
    }

    setLoading(true)
    setSearchResults(null)
    setSelectedReport(null)

    try {
      const response = await axios.get(`/api/reports/legal/search?identifier=${searchTerm.trim()}`)
      setSearchResults(response.data)
      
      if (!response.data.found) {
        toast.warning(response.data.message)
      } else {
        toast.success('Arama başarılı!')
      }
    } catch (error) {
      console.error('Arama hatası:', error)
      if (error.response?.status === 403) {
        toast.error('Bu işlem için admin yetkisi gerekli')
      } else {
        toast.error('Arama yapılamadı')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadMutabakatReport = async (mutabakatId) => {
    setReportLoading(true)
    setSelectedReport(null)

    try {
      const response = await axios.get(`/api/reports/legal/mutabakat/${mutabakatId}`)
      setSelectedReport(response.data)
      toast.success('Rapor yüklendi')
    } catch (error) {
      console.error('Rapor yükleme hatası:', error)
      toast.error('Rapor yüklenemedi')
    } finally {
      setReportLoading(false)
    }
  }

  const loadUserReport = async (userId) => {
    setReportLoading(true)
    setSelectedReport(null)

    try {
      const response = await axios.get(`/api/reports/legal/user/${userId}`)
      setSelectedReport(response.data)
      toast.success('Kullanıcı raporu yüklendi')
    } catch (error) {
      console.error('Rapor yükleme hatası:', error)
      toast.error('Rapor yüklenemedi')
    } finally {
      setReportLoading(false)
    }
  }

  const handlePrint = () => {
    window.print()
  }

  const handleDownloadPDF = async () => {
    if (!selectedReport) {
      toast.error('Rapor seçilmemiş')
      return
    }

    try {
      toast.info('PDF oluşturuluyor... (İmzalanıyor, şifreleniyor)')
      
      let url = ''
      let filename = ''
      
      if (selectedReport.report_type === 'mutabakat') {
        url = `/api/reports/legal/mutabakat/${selectedReport.mutabakat.id}/pdf`
        filename = `Yasal_Rapor_${selectedReport.mutabakat.mutabakat_no}.pdf`
      } else if (selectedReport.report_type === 'user') {
        url = `/api/reports/legal/user/${selectedReport.user.id}/pdf`
        filename = `Yasal_Rapor_Kullanici_${selectedReport.user.vkn_tckn || selectedReport.user.username}.pdf`
      }

      console.log('[PDF DOWNLOAD] URL:', url)
      console.log('[PDF DOWNLOAD] Report type:', selectedReport.report_type)
      console.log('[PDF DOWNLOAD] User ID:', selectedReport.user?.id)
      console.log('[PDF DOWNLOAD] Mutabakat ID:', selectedReport.mutabakat?.id)

      const response = await axios.get(url, {
        responseType: 'blob'
      })
      
      console.log('[PDF DOWNLOAD] Response received:', response.status)
      console.log('[PDF DOWNLOAD] Content length:', response.data.size)

      // PDF hash bilgisini header'dan al
      const pdfHash = response.headers['x-pdf-hash']
      const pdfSecurity = response.headers['x-pdf-security']

      // PDF'i indir
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)

      toast.success(
        <div>
          <strong>PDF İndirildi!</strong>
          <br />
          <small>Dijital İmzalı • 256-bit AES Şifreli</small>
          <br />
          <small style={{fontSize: '0.75em', opacity: 0.8}}>Hash: {pdfHash?.substring(0, 16)}...</small>
        </div>,
        { autoClose: 5000 }
      )
    } catch (error) {
      console.error('[PDF DOWNLOAD] Hata detaylari:', error)
      console.error('[PDF DOWNLOAD] Error response:', error.response)
      console.error('[PDF DOWNLOAD] Error message:', error.message)
      toast.error(`PDF indirilemedi: ${error.response?.status || error.message}`)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString('tr-TR')
  }

  const formatCurrency = (amount) => {
    if (!amount) return '0,00 TL'
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY'
    }).format(amount)
  }

  return (
    <div className="legal-reports">
      <div className="no-print">
        <div className="reports-header">
          <div>
            <h1><FaFileAlt /> Yasal Raporlar</h1>
            <p>Resmi makamlar için detaylı mutabakat ve kullanıcı raporları</p>
          </div>
        </div>

        {/* Arama Formu */}
        <div className="search-section">
          <form onSubmit={handleSearch} className="search-form">
            <div className="search-input-group">
              <FaSearch className="search-icon" />
              <input
                type="text"
                placeholder="VKN / TC Kimlik No veya Mutabakat Numarası"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
              />
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? 'Aranıyor...' : 'Ara'}
              </button>
            </div>
            <p className="search-hint">
              Örnek: 1234567890 (VKN) veya MUT-20231023-ABCD (Mutabakat No)
            </p>
          </form>
        </div>

        {/* Arama Sonuçları */}
        {searchResults && searchResults.found && (
          <div className="search-results">
            {searchResults.search_type === 'vkn' && (
              <div className="user-results">
                <div className="result-header">
                  <FaUser /> Kullanıcı Bilgileri
                </div>
                <div className="user-info-grid">
                  <div className="info-item">
                    <strong>VKN/TC:</strong>
                    <span>{searchResults.user.vkn_tckn}</span>
                  </div>
                  <div className="info-item">
                    <strong>Kullanıcı Adı:</strong>
                    <span>{searchResults.user.username}</span>
                  </div>
                  <div className="info-item">
                    <strong>Ad Soyad:</strong>
                    <span>{searchResults.user.full_name || 'N/A'}</span>
                  </div>
                  <div className="info-item">
                    <strong>Firma:</strong>
                    <span>{searchResults.user.company_name || 'N/A'}</span>
                  </div>
                  <div className="info-item">
                    <strong>Email:</strong>
                    <span>{searchResults.user.email || 'N/A'}</span>
                  </div>
                  <div className="info-item">
                    <strong>Telefon:</strong>
                    <span>{searchResults.user.phone || 'N/A'}</span>
                  </div>
                </div>
                
                <button
                  className="btn btn-success"
                  onClick={() => loadUserReport(searchResults.user.id)}
                  style={{ marginTop: '15px' }}
                >
                  <FaFileAlt /> Kullanıcı İçin Tam Rapor Oluştur
                </button>

                {searchResults.mutabakat_count > 0 && (
                  <div className="mutabakat-list">
                    <h3>Mutabakatlar ({searchResults.mutabakat_count} adet)</h3>
                    <div className="mutabakat-grid">
                      {searchResults.mutabakat_list.map((m) => (
                        <div key={m.id} className="mutabakat-card">
                          <div className="mutabakat-card-header">
                            <span className="mutabakat-no">{m.mutabakat_no}</span>
                            <span className={`badge badge-${m.durum}`}>{m.durum}</span>
                          </div>
                          <div className="mutabakat-card-body">
                            <p><strong>Bakiye:</strong> {formatCurrency(m.bakiye)}</p>
                            <p><strong>Borç:</strong> {formatCurrency(m.toplam_borc)}</p>
                            <p><strong>Alacak:</strong> {formatCurrency(m.toplam_alacak)}</p>
                            <p><strong>Dönem:</strong> {formatDate(m.donem_baslangic)} - {formatDate(m.donem_bitis)}</p>
                            <p><strong>Rol:</strong> {m.role === 'sender' ? 'Gönderen' : 'Alıcı'}</p>
                          </div>
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => loadMutabakatReport(m.id)}
                          >
                            Detaylı Rapor
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {searchResults.search_type === 'mutabakat_no' && (
              <div className="mutabakat-found">
                <div className="result-header">
                  <FaFileAlt /> Mutabakat Bulundu
                </div>
                <p>Mutabakat Numarası: <strong>{searchResults.mutabakat_no}</strong></p>
                <button
                  className="btn btn-primary"
                  onClick={() => loadMutabakatReport(searchResults.mutabakat_id)}
                >
                  <FaFileAlt /> Detaylı Yasal Rapor Oluştur
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Rapor Görüntüleme */}
      {reportLoading && (
        <div className="report-loading no-print">
          <div className="spinner"></div>
          <p>Rapor oluşturuluyor...</p>
        </div>
      )}

      {selectedReport && (
        <div className="legal-report-container">
          <div className="no-print report-actions">
            <button className="btn btn-success" onClick={handleDownloadPDF}>
              <FaDownload /> İmzalı PDF İndir
            </button>
            <button className="btn btn-primary" onClick={handlePrint}>
              <FaPrint /> Yazdır
            </button>
          </div>

          <div className="legal-report printable">
            {/* Rapor Başlığı */}
            <div className="report-header-legal">
              <h1>🏛️ YASAL RAPOR</h1>
              <h2>Resmi Makamlar İçin Detaylı Bilgi Dökümanı</h2>
              <div className="report-meta">
                <p><strong>Rapor Tarihi:</strong> {formatDate(selectedReport.report_generated_at)}</p>
                <p><strong>Raporu Oluşturan:</strong> {selectedReport.generated_by.full_name || selectedReport.generated_by.username}</p>
              </div>
            </div>

            {/* Mutabakat Raporu */}
            {selectedReport.mutabakat && (
              <div className="report-section">
                <h2 className="section-title">📄 MUTABAKAT BİLGİLERİ</h2>
                <table className="report-table">
                  <tbody>
                    <tr>
                      <th>Mutabakat Numarası</th>
                      <td>{selectedReport.mutabakat.mutabakat_no}</td>
                    </tr>
                    <tr>
                      <th>Durum</th>
                      <td><span className={`badge badge-${selectedReport.mutabakat.durum}`}>{selectedReport.mutabakat.durum}</span></td>
                    </tr>
                    <tr>
                      <th>Bakiye</th>
                      <td>{formatCurrency(selectedReport.mutabakat.bakiye)}</td>
                    </tr>
                    <tr>
                      <th>Toplam Borç</th>
                      <td>{formatCurrency(selectedReport.mutabakat.toplam_borc)}</td>
                    </tr>
                    <tr>
                      <th>Toplam Alacak</th>
                      <td>{formatCurrency(selectedReport.mutabakat.toplam_alacak)}</td>
                    </tr>
                    <tr>
                      <th>Bayi Sayısı</th>
                      <td>{selectedReport.mutabakat.toplam_bayi_sayisi}</td>
                    </tr>
                    <tr>
                      <th>Dönem</th>
                      <td>
                        {formatDate(selectedReport.mutabakat.donem_baslangic)} - {formatDate(selectedReport.mutabakat.donem_bitis)}
                      </td>
                    </tr>
                    <tr>
                      <th>Oluşturulma Tarihi</th>
                      <td>{formatDate(selectedReport.mutabakat.created_at)}</td>
                    </tr>
                    {selectedReport.mutabakat.pdf_file_path && (
                      <tr>
                        <th>PDF Dosyası</th>
                        <td>{selectedReport.mutabakat.pdf_file_path}</td>
                      </tr>
                    )}
                  </tbody>
                </table>

                {/* Gönderen ve Alıcı */}
                <div className="parties-grid">
                  {selectedReport.sender && (
                    <div className="party-info">
                      <h3><FaBuilding /> Gönderen</h3>
                      <table className="report-table">
                        <tbody>
                          <tr><th>VKN/TC</th><td>{selectedReport.sender.vkn_tckn}</td></tr>
                          <tr><th>Ad Soyad</th><td>{selectedReport.sender.full_name || 'N/A'}</td></tr>
                          <tr><th>Firma</th><td>{selectedReport.sender.company_name || 'N/A'}</td></tr>
                          <tr><th>Email</th><td>{selectedReport.sender.email || 'N/A'}</td></tr>
                          <tr><th>Telefon</th><td>{selectedReport.sender.phone || 'N/A'}</td></tr>
                        </tbody>
                      </table>
                    </div>
                  )}

                  {selectedReport.receiver && (
                    <div className="party-info">
                      <h3><FaBuilding /> Alıcı</h3>
                      <table className="report-table">
                        <tbody>
                          <tr><th>VKN/TC</th><td>{selectedReport.receiver.vkn_tckn}</td></tr>
                          <tr><th>Ad Soyad</th><td>{selectedReport.receiver.full_name || 'N/A'}</td></tr>
                          <tr><th>Firma</th><td>{selectedReport.receiver.company_name || 'N/A'}</td></tr>
                          <tr><th>Email</th><td>{selectedReport.receiver.email || 'N/A'}</td></tr>
                          <tr><th>Telefon</th><td>{selectedReport.receiver.phone || 'N/A'}</td></tr>
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {/* Activity Logları */}
                {selectedReport.activity_logs && selectedReport.activity_logs.length > 0 && (
                  <div className="logs-section">
                    <h3>📋 İŞLEM LOGLAR ({selectedReport.activity_logs.length} adet)</h3>
                    <table className="logs-table">
                      <thead>
                        <tr>
                          <th>Tarih</th>
                          <th>İşlem</th>
                          <th>Açıklama</th>
                          <th>IP Adresi</th>
                          <th>ISP</th>
                          <th>Konum</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedReport.activity_logs.map((log) => (
                          <tr key={log.id}>
                            <td>{formatDate(log.timestamp)}</td>
                            <td>{log.action}</td>
                            <td>{log.description}</td>
                            <td>{log.ip_address || 'N/A'}</td>
                            <td>{log.isp || 'N/A'}</td>
                            <td>{log.city && log.country ? `${log.city}, ${log.country}` : 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* KVKK Onayları */}
                <div className="kvkk-section">
                  <h3><FaShieldAlt /> KVKK ONAYLARI</h3>
                  <div className="kvkk-grid">
                    {selectedReport.kvkk_consents.sender.exists && (
                      <div className="kvkk-party">
                        <h4>Gönderen KVKK Onayları</h4>
                        <table className="report-table">
                          <tbody>
                            <tr>
                              <th>KVKK Politikası</th>
                              <td>
                                {selectedReport.kvkk_consents.sender.data.kvkk_policy_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                {selectedReport.kvkk_consents.sender.data.kvkk_policy_date_str && (
                                  <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                    ({selectedReport.kvkk_consents.sender.data.kvkk_policy_date_str})
                                  </span>
                                )}
                              </td>
                            </tr>
                            <tr>
                              <th>Müşteri Aydınlatma</th>
                              <td>
                                {selectedReport.kvkk_consents.sender.data.customer_notice_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                {selectedReport.kvkk_consents.sender.data.customer_notice_date_str && (
                                  <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                    ({selectedReport.kvkk_consents.sender.data.customer_notice_date_str})
                                  </span>
                                )}
                              </td>
                            </tr>
                            <tr>
                              <th>Veri Saklama</th>
                              <td>
                                {selectedReport.kvkk_consents.sender.data.data_retention_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                {selectedReport.kvkk_consents.sender.data.data_retention_date_str && (
                                  <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                    ({selectedReport.kvkk_consents.sender.data.data_retention_date_str})
                                  </span>
                                )}
                              </td>
                            </tr>
                            <tr>
                              <th>Sistem Onayı</th>
                              <td>
                                {selectedReport.kvkk_consents.sender.data.system_consent_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                {selectedReport.kvkk_consents.sender.data.system_consent_date_str && (
                                  <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                    ({selectedReport.kvkk_consents.sender.data.system_consent_date_str})
                                  </span>
                                )}
                              </td>
                            </tr>
                            <tr><th>IP Adresi</th><td>{selectedReport.kvkk_consents.sender.data.ip_address || 'N/A'}</td></tr>
                            <tr><th>ISP</th><td>{selectedReport.kvkk_consents.sender.data.isp || 'N/A'}</td></tr>
                            <tr><th>Konum</th><td>{selectedReport.kvkk_consents.sender.data.city || 'N/A'}, {selectedReport.kvkk_consents.sender.data.country || 'N/A'}</td></tr>
                            <tr><th>İlk Onay Tarihi</th><td>{selectedReport.kvkk_consents.sender.data.created_at_str || formatDate(selectedReport.kvkk_consents.sender.data.created_at)}</td></tr>
                          </tbody>
                        </table>
                      </div>
                    )}

                    {selectedReport.kvkk_consents.receiver.exists && (
                      <div className="kvkk-party">
                        <h4>Alıcı KVKK Onayları</h4>
                        <table className="report-table">
                          <tbody>
                            <tr>
                              <th>KVKK Politikası</th>
                              <td>
                                {selectedReport.kvkk_consents.receiver.data.kvkk_policy_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                {selectedReport.kvkk_consents.receiver.data.kvkk_policy_date_str && (
                                  <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                    ({selectedReport.kvkk_consents.receiver.data.kvkk_policy_date_str})
                                  </span>
                                )}
                              </td>
                            </tr>
                            <tr>
                              <th>Müşteri Aydınlatma</th>
                              <td>
                                {selectedReport.kvkk_consents.receiver.data.customer_notice_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                {selectedReport.kvkk_consents.receiver.data.customer_notice_date_str && (
                                  <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                    ({selectedReport.kvkk_consents.receiver.data.customer_notice_date_str})
                                  </span>
                                )}
                              </td>
                            </tr>
                            <tr>
                              <th>Veri Saklama</th>
                              <td>
                                {selectedReport.kvkk_consents.receiver.data.data_retention_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                {selectedReport.kvkk_consents.receiver.data.data_retention_date_str && (
                                  <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                    ({selectedReport.kvkk_consents.receiver.data.data_retention_date_str})
                                  </span>
                                )}
                              </td>
                            </tr>
                            <tr>
                              <th>Sistem Onayı</th>
                              <td>
                                {selectedReport.kvkk_consents.receiver.data.system_consent_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                {selectedReport.kvkk_consents.receiver.data.system_consent_date_str && (
                                  <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                    ({selectedReport.kvkk_consents.receiver.data.system_consent_date_str})
                                  </span>
                                )}
                              </td>
                            </tr>
                            <tr><th>IP Adresi</th><td>{selectedReport.kvkk_consents.receiver.data.ip_address || 'N/A'}</td></tr>
                            <tr><th>ISP</th><td>{selectedReport.kvkk_consents.receiver.data.isp || 'N/A'}</td></tr>
                            <tr><th>Konum</th><td>{selectedReport.kvkk_consents.receiver.data.city || 'N/A'}, {selectedReport.kvkk_consents.receiver.data.country || 'N/A'}</td></tr>
                            <tr><th>İlk Onay Tarihi</th><td>{selectedReport.kvkk_consents.receiver.data.created_at_str || formatDate(selectedReport.kvkk_consents.receiver.data.created_at)}</td></tr>
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>

                  {/* KVKK Silme Logları */}
                  {(selectedReport.kvkk_deletion_logs.sender.length > 0 || selectedReport.kvkk_deletion_logs.receiver.length > 0) && (
                    <div className="kvkk-deletions">
                      <h4><FaExclamationTriangle /> KVKK Onay Silme Kayıtları</h4>
                      {selectedReport.kvkk_deletion_logs.sender.length > 0 && (
                        <div>
                          <strong>Gönderen:</strong>
                          <table className="report-table deletion-log-table">
                            <thead>
                              <tr>
                                <th>Silen Admin</th>
                                <th>Silme Nedeni</th>
                                <th>Silme IP / ISP</th>
                                <th>Orijinal Onay IP / ISP</th>
                                <th>Silme Tarihi</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedReport.kvkk_deletion_logs.sender.map((log) => (
                                <tr key={log.id}>
                                  <td><strong>{log.deleted_by_username}</strong></td>
                                  <td>{log.deletion_reason || 'Belirtilmemiş'}</td>
                                  <td>
                                    <div style={{fontSize: '0.9em'}}>
                                      <div><strong>IP:</strong> {log.deletion_ip_address || 'N/A'}</div>
                                      <div><strong>ISP:</strong> {log.deletion_isp || 'N/A'}</div>
                                    </div>
                                  </td>
                                  <td>
                                    <div style={{fontSize: '0.9em'}}>
                                      <div><strong>IP:</strong> {log.original_ip_address || 'N/A'}</div>
                                      <div><strong>ISP:</strong> {log.original_isp || 'N/A'}</div>
                                    </div>
                                  </td>
                                  <td>{log.deleted_at_str || formatDate(log.deleted_at)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                      {selectedReport.kvkk_deletion_logs.receiver.length > 0 && (
                        <div>
                          <strong>Alıcı:</strong>
                          <table className="report-table deletion-log-table">
                            <thead>
                              <tr>
                                <th>Silen Admin</th>
                                <th>Silme Nedeni</th>
                                <th>Silme IP / ISP</th>
                                <th>Orijinal Onay IP / ISP</th>
                                <th>Silme Tarihi</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedReport.kvkk_deletion_logs.receiver.map((log) => (
                                <tr key={log.id}>
                                  <td><strong>{log.deleted_by_username}</strong></td>
                                  <td>{log.deletion_reason || 'Belirtilmemiş'}</td>
                                  <td>
                                    <div style={{fontSize: '0.9em'}}>
                                      <div><strong>IP:</strong> {log.deletion_ip_address || 'N/A'}</div>
                                      <div><strong>ISP:</strong> {log.deletion_isp || 'N/A'}</div>
                                    </div>
                                  </td>
                                  <td>
                                    <div style={{fontSize: '0.9em'}}>
                                      <div><strong>IP:</strong> {log.original_ip_address || 'N/A'}</div>
                                      <div><strong>ISP:</strong> {log.original_isp || 'N/A'}</div>
                                    </div>
                                  </td>
                                  <td>{log.deleted_at_str || formatDate(log.deleted_at)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Kullanıcı Raporu */}
            {selectedReport.user && (
              <div className="report-section">
                <h2 className="section-title"><FaUser /> KULLANICI BİLGİLERİ</h2>
                <table className="report-table">
                  <tbody>
                    <tr><th>VKN/TC</th><td>{selectedReport.user.vkn_tckn}</td></tr>
                    <tr><th>Kullanıcı Adı</th><td>{selectedReport.user.username}</td></tr>
                    <tr><th>Ad Soyad</th><td>{selectedReport.user.full_name || 'N/A'}</td></tr>
                    <tr><th>Firma</th><td>{selectedReport.user.company_name || 'N/A'}</td></tr>
                    <tr><th>Email</th><td>{selectedReport.user.email || 'N/A'}</td></tr>
                    <tr><th>Telefon</th><td>{selectedReport.user.phone || 'N/A'}</td></tr>
                    <tr><th>Adres</th><td>{selectedReport.user.address || 'N/A'}</td></tr>
                    <tr><th>Rol</th><td>{selectedReport.user.role}</td></tr>
                    <tr><th>Durum</th><td>{selectedReport.user.is_active ? 'Aktif' : 'Pasif'}</td></tr>
                    <tr><th>Kayıt Tarihi</th><td>{formatDate(selectedReport.user.created_at)}</td></tr>
                  </tbody>
                </table>

                <div className="statistics-grid">
                  <div className="stat-box">
                    <div className="stat-value">{selectedReport.statistics.total_mutabakats}</div>
                    <div className="stat-label">Toplam Mutabakat</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-value">{selectedReport.statistics.total_activity_logs}</div>
                    <div className="stat-label">Toplam İşlem Logu</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-value">{selectedReport.statistics.kvkk_consent_exists ? '✅' : '❌'}</div>
                    <div className="stat-label">KVKK Onayı</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-value">{selectedReport.statistics.kvkk_deletions_count}</div>
                    <div className="stat-label">KVKK Silme Sayısı</div>
                  </div>
                </div>

                {selectedReport.mutabakats && selectedReport.mutabakats.length > 0 && (
                  <div className="user-mutabakats">
                    <h3>📋 Mutabakatlar ({selectedReport.mutabakats.length} adet)</h3>
                    <table className="report-table">
                      <thead>
                        <tr>
                          <th>Mutabakat No</th>
                          <th>Durum</th>
                          <th>Bakiye</th>
                          <th>Borç</th>
                          <th>Alacak</th>
                          <th>Dönem</th>
                          <th>Rol</th>
                          <th>Tarih</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedReport.mutabakats.map((m) => (
                          <tr key={m.id}>
                            <td>{m.mutabakat_no}</td>
                            <td><span className={`badge badge-${m.durum}`}>{m.durum}</span></td>
                            <td>{formatCurrency(m.bakiye)}</td>
                            <td>{formatCurrency(m.toplam_borc)}</td>
                            <td>{formatCurrency(m.toplam_alacak)}</td>
                            <td>{formatDate(m.donem_baslangic)} - {formatDate(m.donem_bitis)}</td>
                            <td>{m.role === 'sender' ? 'Gönderen' : 'Alıcı'}</td>
                            <td>{formatDate(m.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Gönderen ve Alıcı */}
                <div className="parties-grid" style={{marginTop: '30px'}}>
                  {selectedReport.sender && (
                    <div className="party-info">
                      <h3><FaBuilding /> Gönderen</h3>
                      <table className="report-table">
                        <tbody>
                          <tr><th>VKN/TC</th><td>{selectedReport.sender.vkn_tckn}</td></tr>
                          <tr><th>Ad Soyad</th><td>{selectedReport.sender.full_name || 'N/A'}</td></tr>
                          <tr><th>Firma</th><td>{selectedReport.sender.company_name || 'N/A'}</td></tr>
                          <tr><th>Email</th><td>{selectedReport.sender.email || 'N/A'}</td></tr>
                          <tr><th>Telefon</th><td>{selectedReport.sender.phone || 'N/A'}</td></tr>
                        </tbody>
                      </table>
                    </div>
                  )}

                  {selectedReport.receiver && (
                    <div className="party-info">
                      <h3><FaBuilding /> Alıcı</h3>
                      <table className="report-table">
                        <tbody>
                          <tr><th>VKN/TC</th><td>{selectedReport.receiver.vkn_tckn}</td></tr>
                          <tr><th>Ad Soyad</th><td>{selectedReport.receiver.full_name || 'N/A'}</td></tr>
                          <tr><th>Firma</th><td>{selectedReport.receiver.company_name || 'N/A'}</td></tr>
                          <tr><th>Email</th><td>{selectedReport.receiver.email || 'N/A'}</td></tr>
                          <tr><th>Telefon</th><td>{selectedReport.receiver.phone || 'N/A'}</td></tr>
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {selectedReport.activity_logs && selectedReport.activity_logs.length > 0 && (
                  <div className="logs-section">
                    <h3>📋 İŞLEM LOGLARI ({selectedReport.activity_logs.length} adet)</h3>
                    <table className="logs-table">
                      <thead>
                        <tr>
                          <th>Tarih</th>
                          <th>İşlem</th>
                          <th>Açıklama</th>
                          <th>IP</th>
                          <th>ISP</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedReport.activity_logs.map((log) => (
                          <tr key={log.id}>
                            <td>{formatDate(log.timestamp)}</td>
                            <td>{log.action}</td>
                            <td>{log.description}</td>
                            <td>{log.ip_address || 'N/A'}</td>
                            <td>{log.isp || 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* KVKK Onayları */}
                {selectedReport.kvkk_consents && (
                  <div className="kvkk-section">
                    <h3><FaShieldAlt /> KVKK ONAYLARI</h3>
                    <div className="kvkk-grid">
                      {selectedReport.kvkk_consents.receiver && selectedReport.kvkk_consents.receiver.exists && (
                        <div className="kvkk-party">
                          <h4>Alıcı KVKK Onayları</h4>
                          <table className="report-table">
                            <tbody>
                              <tr>
                                <th>KVKK Politikası</th>
                                <td>
                                  {selectedReport.kvkk_consents.receiver.data.kvkk_policy_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                  {selectedReport.kvkk_consents.receiver.data.kvkk_policy_date_str && (
                                    <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                      ({selectedReport.kvkk_consents.receiver.data.kvkk_policy_date_str})
                                    </span>
                                  )}
                                </td>
                              </tr>
                              <tr>
                                <th>Müşteri Aydınlatma</th>
                                <td>
                                  {selectedReport.kvkk_consents.receiver.data.customer_notice_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                  {selectedReport.kvkk_consents.receiver.data.customer_notice_date_str && (
                                    <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                      ({selectedReport.kvkk_consents.receiver.data.customer_notice_date_str})
                                    </span>
                                  )}
                                </td>
                              </tr>
                              <tr>
                                <th>Veri Saklama</th>
                                <td>
                                  {selectedReport.kvkk_consents.receiver.data.data_retention_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                  {selectedReport.kvkk_consents.receiver.data.data_retention_date_str && (
                                    <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                      ({selectedReport.kvkk_consents.receiver.data.data_retention_date_str})
                                    </span>
                                  )}
                                </td>
                              </tr>
                              <tr>
                                <th>Sistem Onayı</th>
                                <td>
                                  {selectedReport.kvkk_consents.receiver.data.system_consent_accepted ? '✅ Onaylı' : '❌ Onaylanmamış'}
                                  {selectedReport.kvkk_consents.receiver.data.system_consent_date_str && (
                                    <span style={{marginLeft: '10px', fontSize: '0.9em', color: '#666'}}>
                                      ({selectedReport.kvkk_consents.receiver.data.system_consent_date_str})
                                    </span>
                                  )}
                                </td>
                              </tr>
                              <tr><th>IP Adresi</th><td>{selectedReport.kvkk_consents.receiver.data.ip_address || 'N/A'}</td></tr>
                              <tr><th>ISP</th><td>{selectedReport.kvkk_consents.receiver.data.isp || 'N/A'}</td></tr>
                              <tr><th>Konum</th><td>{selectedReport.kvkk_consents.receiver.data.city || 'N/A'}, {selectedReport.kvkk_consents.receiver.data.country || 'N/A'}</td></tr>
                              <tr><th>İlk Onay Tarihi</th><td>{selectedReport.kvkk_consents.receiver.data.created_at_str || formatDate(selectedReport.kvkk_consents.receiver.data.created_at)}</td></tr>
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>

                    {/* KVKK Silme Logları */}
                    {selectedReport.kvkk_deletion_logs && (selectedReport.kvkk_deletion_logs.sender?.length > 0 || selectedReport.kvkk_deletion_logs.receiver?.length > 0) && (
                      <div className="kvkk-deletions">
                        <h4><FaExclamationTriangle /> KVKK Onay Silme Kayıtları</h4>
                        {selectedReport.kvkk_deletion_logs.receiver && selectedReport.kvkk_deletion_logs.receiver.length > 0 && (
                          <div>
                            <strong>Alıcı:</strong>
                            <table className="report-table deletion-log-table">
                              <thead>
                                <tr>
                                  <th>Silen Admin</th>
                                  <th>Silme Nedeni</th>
                                  <th>Silme IP / ISP</th>
                                  <th>Orijinal Onay IP / ISP</th>
                                  <th>Silme Tarihi</th>
                                </tr>
                              </thead>
                              <tbody>
                                {selectedReport.kvkk_deletion_logs.receiver.map((log) => (
                                  <tr key={log.id}>
                                    <td><strong>{log.deleted_by_username}</strong></td>
                                    <td>{log.deletion_reason || 'Belirtilmemiş'}</td>
                                    <td>
                                      <div style={{fontSize: '0.9em'}}>
                                        <div><strong>IP:</strong> {log.deletion_ip_address || 'N/A'}</div>
                                        <div><strong>ISP:</strong> {log.deletion_isp || 'N/A'}</div>
                                      </div>
                                    </td>
                                    <td>
                                      <div style={{fontSize: '0.9em'}}>
                                        <div><strong>IP:</strong> {log.original_ip_address || 'N/A'}</div>
                                        <div><strong>ISP:</strong> {log.original_isp || 'N/A'}</div>
                                      </div>
                                    </td>
                                    <td>{log.deleted_at_str || formatDate(log.deleted_at)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Rapor Sonuç */}
            <div className="report-footer-legal">
              <p className="legal-disclaimer">
                <strong>⚖️ YASAL UYARI:</strong> Bu rapor resmi makamlar tarafından talep edilen yasal delil niteliğindeki bilgileri içermektedir. 
                Tüm IP adresleri, ISP bilgileri, işlem logları ve KVKK onayları yasal süreçlerde kullanılmak üzere hazırlanmıştır.
              </p>
              <div className="report-signature">
                <p>Rapor Tarihi: {formatDate(selectedReport.report_generated_at)}</p>
                <p>Hazırlayan: {selectedReport.generated_by.full_name || selectedReport.generated_by.username}</p>
                <p className="signature-line">İmza: _________________</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

