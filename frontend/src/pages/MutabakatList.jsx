import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'
import { format } from 'date-fns'
import { tr } from 'date-fns/locale'
import { FaEye, FaPlus, FaFilter, FaPaperPlane, FaFilePdf } from 'react-icons/fa'
import { showNotification } from '../components/Notification'
import SkeletonLoader from '../components/SkeletonLoader'
import LoadingButton from '../components/LoadingButton'
import FilterPanel, { FilterGroup, FilterItem } from '../components/FilterPanel'
import DateRangePicker from '../components/DateRangePicker'
import AmountRangeSlider from '../components/AmountRangeSlider'
import FilterBadges from '../components/FilterBadges'
import PDFPreviewModal from '../components/PDFPreviewModal'
import MutabakatMobileCard from '../components/MutabakatMobileCard'
import './MutabakatList.css'

export default function MutabakatList() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [filterDurum, setFilterDurum] = useState('') // Durum filtresi
  const [sendingId, setSendingId] = useState(null) // Gönderilen mutabakat ID
  
  // Pagination state
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [searchTerm, setSearchTerm] = useState('')
  
  // Advanced Filter States
  const [filterPanelOpen, setFilterPanelOpen] = useState(false)
  const [dateStart, setDateStart] = useState('')
  const [dateEnd, setDateEnd] = useState('')
  const [amountMin, setAmountMin] = useState(null)
  const [amountMax, setAmountMax] = useState(null)
  const [selectedCompany, setSelectedCompany] = useState('')
  
  // PDF Preview states
  const [showPDFPreview, setShowPDFPreview] = useState(false)
  const [pdfUrl, setPdfUrl] = useState(null)
  const [selectedMutabakat, setSelectedMutabakat] = useState(null)
  
  const { data: mutabakatsData, isLoading } = useQuery({
    queryKey: ['mutabakats', page, pageSize, searchTerm, filterDurum, dateStart, dateEnd, amountMin, amountMax, selectedCompany],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      
      if (searchTerm) params.append('search', searchTerm)
      if (filterDurum) params.append('durum', filterDurum)
      if (dateStart) params.append('date_start', dateStart)
      if (dateEnd) params.append('date_end', dateEnd)
      if (amountMin !== null) params.append('amount_min', amountMin)
      if (amountMax !== null) params.append('amount_max', amountMax)
      if (selectedCompany) params.append('company', selectedCompany)
      
      const response = await axios.get(`/api/mutabakat/?${params.toString()}`)
      return response.data
    }
  })
  
  const mutabakats = mutabakatsData?.items || []
  const metadata = mutabakatsData?.metadata || { total_pages: 0, total_items: 0, has_next: false, has_prev: false }

  // Mutabakat gönderme mutation
  const sendMutabakat = useMutation({
    mutationFn: async (mutabakatId) => {
      const response = await axios.post(`/api/mutabakat/${mutabakatId}/send`)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries(['mutabakats'])
      
      // Modern notification ile göster
      showNotification(
        `✅ Mutabakat başarıyla gönderildi!\n\n📱 ${data.message || 'SMS gönderildi'}`,
        'success',
        6000
      )
      setSendingId(null)
    },
    onError: (error) => {
      showNotification(
        `❌ ${error.response?.data?.detail || 'Mutabakat gönderilemedi'}`,
        'error',
        5000
      )
      setSendingId(null)
    }
  })

  // Toplu gönderim mutation
  const sendAllDrafts = useMutation({
    mutationFn: async () => {
      const response = await axios.post('/api/mutabakat/send-all-drafts')
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries(['mutabakats'])
      
      showNotification(
        `✅ ${data.sent_count} mutabakat başarıyla gönderildi!${data.failed_count > 0 ? `\n⚠️ ${data.failed_count} hata` : ''}`,
        data.failed_count > 0 ? 'warning' : 'success',
        7000
      )
    },
    onError: (error) => {
      showNotification(
        `❌ ${error.response?.data?.detail || 'Toplu gönderim başarısız'}`,
        'error',
        5000
      )
    }
  })

  const handleSendMutabakat = (mutabakatId, mutabakatNo) => {
    if (window.confirm(`"${mutabakatNo}" nolu mutabakat müşteriye gönderilecek. Emin misiniz?`)) {
      setSendingId(mutabakatId)
      sendMutabakat.mutate(mutabakatId)
    }
  }

  const handleSendAllDrafts = () => {
    const draftCount = mutabakats?.filter(m => m.durum === 'taslak').length || 0
    
    if (draftCount === 0) {
      showNotification('ℹ️ Gönderilecek taslak mutabakat bulunamadı', 'info', 3000)
      return
    }
    
    if (window.confirm(`${draftCount} adet taslak mutabakat toplu olarak gönderilecek. Emin misiniz?`)) {
      sendAllDrafts.mutate()
    }
  }

  // PDF Preview Handler
  const handlePreviewPDF = async (mutabakat) => {
    try {
      const response = await axios.get(`/api/mutabakat/${mutabakat.id}/download-pdf`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      setPdfUrl(url)
      setSelectedMutabakat(mutabakat)
      setShowPDFPreview(true)
    } catch (error) {
      showNotification(
        `❌ PDF yüklenemedi: ${error.response?.data?.detail || 'Bilinmeyen hata'}`,
        'error',
        3000
      )
    }
  }

  // Rol kontrolü
  const canCreateMutabakat = ['admin', 'company_admin', 'muhasebe', 'planlama'].includes(user?.role)
  const isCustomer = ['musteri', 'tedarikci'].includes(user?.role) // Müşteri veya Tedarikçi
  const isInternal = ['admin', 'company_admin', 'muhasebe', 'planlama'].includes(user?.role) // Şirket içi kullanıcılar

  const getDurumBadge = (durum) => {
    const badges = {
      taslak: 'badge-secondary',
      gonderildi: 'badge-warning',
      onaylandi: 'badge-success',
      reddedildi: 'badge-danger',
      iptal: 'badge-secondary'
    }
    return badges[durum] || 'badge-secondary'
  }

  const getDurumText = (durum) => {
    const texts = {
      taslak: 'Taslak',
      gonderildi: 'Gönderildi',
      onaylandi: 'Onaylandı',
      reddedildi: 'Reddedildi',
      iptal: 'İptal'
    }
    return texts[durum] || durum
  }

  // Advanced Filter Helpers
  const getActiveFilters = () => {
    const filters = []
    if (dateStart || dateEnd) {
      const dateText = dateStart && dateEnd 
        ? `${dateStart} - ${dateEnd}` 
        : dateStart || dateEnd
      filters.push({ key: 'date', label: 'Tarih', value: dateText })
    }
    if (amountMin !== null || amountMax !== null) {
      const amountText = `₺${(amountMin || 0).toLocaleString('tr-TR')} - ₺${(amountMax || 1000000).toLocaleString('tr-TR')}`
      filters.push({ key: 'amount', label: 'Tutar', value: amountText })
    }
    if (selectedCompany) {
      filters.push({ key: 'company', label: 'Şirket', value: selectedCompany })
    }
    if (filterDurum) {
      filters.push({ key: 'durum', label: 'Durum', value: getDurumText(filterDurum) })
    }
    return filters
  }

  const clearAllFilters = () => {
    setDateStart('')
    setDateEnd('')
    setAmountMin(null)
    setAmountMax(null)
    setSelectedCompany('')
    setFilterDurum('')
    setPage(1)
  }

  const removeFilter = (filterKey) => {
    switch(filterKey) {
      case 'date':
        setDateStart('')
        setDateEnd('')
        break
      case 'amount':
        setAmountMin(null)
        setAmountMax(null)
        break
      case 'company':
        setSelectedCompany('')
        break
      case 'durum':
        setFilterDurum('')
        break
    }
    setPage(1)
  }

  const activeFilters = getActiveFilters()
  const activeFilterCount = activeFilters.length

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY'
    }).format(amount || 0)
  }

  // Müşteriye özel bilgi mesajı
  const getCustomerMessage = () => {
    const bekleyen = mutabakats?.filter(m => 
      m.durum === 'gonderildi' && m.receiver_id === user?.id
    ).length || 0
    
    if (bekleyen > 0) {
      return (
        <div className="customer-alert alert-warning">
          <strong>📢 {bekleyen} adet mutabakat onayınızı bekliyor!</strong>
          <p>Lütfen "Gönderildi" durumundaki mutabakatları inceleyin ve onaylayın veya reddedin.</p>
        </div>
      )
    }
    
    return (
      <div className="customer-alert alert-info">
        <strong>ℹ️ Mutabakat Nasıl Onaylanır?</strong>
        <p>1. "Gönderildi" durumundaki mutabakatı seçin</p>
        <p>2. "Görüntüle" butonuna tıklayın</p>
        <p>3. Detayları inceleyin</p>
        <p>4. "Onayla" veya "Reddet" butonunu kullanın</p>
      </div>
    )
  }

  // Backend artık filtreleme yapıyor, filteredMutabakats'a gerek yok
  // Durum sayıları metadata'dan geliyor olabilir ama şimdilik client-side hesaplayalım
  const durumCounts = {
    all: metadata.total_items || 0,
    taslak: mutabakats?.filter(m => m.durum === 'taslak').length || 0,
    gonderildi: mutabakats?.filter(m => m.durum === 'gonderildi').length || 0,
    onaylandi: mutabakats?.filter(m => m.durum === 'onaylandi').length || 0,
    reddedildi: mutabakats?.filter(m => m.durum === 'reddedildi').length || 0
  }

  if (isLoading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="mutabakat-list">
      <div className="list-header">
        <div className="list-header-left">
          <h1>📋 Mutabakatlar</h1>
          <p>
            {isCustomer 
              ? 'Size gönderilen mutabakatları görüntüleyin ve yanıt verin'
              : 'Tüm mutabakat belgelerinizi görüntüleyin'
            }
          </p>
        </div>
        <div className="list-header-actions">
          {canCreateMutabakat && (
            <>
              <Link to="/mutabakat/new" className="btn btn-primary btn-create">
                <FaPlus /> Yeni Mutabakat
              </Link>
              {durumCounts.taslak > 0 && (
                <LoadingButton
                  onClick={handleSendAllDrafts}
                  loading={sendAllDrafts.isPending}
                  variant="success"
                  icon={<FaPaperPlane />}
                  loadingText="Gönderiliyor..."
                  title="Tüm taslak mutabakatları toplu olarak gönder"
                >
                  Toplu Gönder ({durumCounts.taslak})
                </LoadingButton>
              )}
            </>
          )}
        </div>
      </div>

      {/* Active Filter Badges */}
      {activeFilterCount > 0 && (
        <FilterBadges
          filters={activeFilters}
          onRemove={removeFilter}
          onClearAll={clearAllFilters}
        />
      )}

      {/* Advanced Filter Panel */}
      <FilterPanel
        title="Gelişmiş Filtreler"
        isOpen={filterPanelOpen}
        onToggle={setFilterPanelOpen}
        onClear={clearAllFilters}
        activeFilterCount={activeFilterCount}
      >
        <FilterGroup label="Tarih Aralığı" columns={1}>
          <DateRangePicker
            startDate={dateStart}
            endDate={dateEnd}
            onStartDateChange={setDateStart}
            onEndDateChange={setDateEnd}
            presets={true}
          />
        </FilterGroup>

        <FilterGroup label="Tutar Aralığı" columns={1}>
          <AmountRangeSlider
            min={0}
            max={10000000}
            step={10000}
            minValue={amountMin}
            maxValue={amountMax}
            onChange={({ min, max }) => {
              setAmountMin(min)
              setAmountMax(max)
              setPage(1)
            }}
            showInputs={true}
          />
        </FilterGroup>

        <FilterGroup label="Diğer Filtreler" columns={2}>
          <FilterItem label="Şirket">
            <input
              type="text"
              placeholder="Şirket ara..."
              value={selectedCompany}
              onChange={(e) => {
                setSelectedCompany(e.target.value)
                setPage(1)
              }}
            />
          </FilterItem>

          <FilterItem label="Durum">
            <select
              value={filterDurum}
              onChange={(e) => {
                setFilterDurum(e.target.value)
                setPage(1)
              }}
            >
              <option value="">Tüm Durumlar</option>
              {!isCustomer && <option value="taslak">Taslak</option>}
              <option value="gonderildi">Gönderildi</option>
              <option value="onaylandi">Onaylandı</option>
              <option value="reddedildi">Reddedildi</option>
            </select>
          </FilterItem>
        </FilterGroup>
      </FilterPanel>

      {/* Filtreler ve Arama */}
      <div className="filter-section">
        {/* Arama */}
        <div className="filter-group" style={{ flex: '1', minWidth: '250px' }}>
          <input
            type="text"
            placeholder="Ara (mutabakat no, VKN, firma adı, açıklama)..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value)
              setPage(1)
            }}
            style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid #ddd' }}
          />
        </div>
        
        {/* Durum Filtresi */}
        <div className="filter-group">
          <div className="filter-label">
            <FaFilter /> <strong>Durum:</strong>
          </div>
          <div className="filter-buttons">
            <button 
              className={`filter-btn ${filterDurum === '' ? 'active' : ''}`}
              onClick={() => {
                setFilterDurum('')
                setPage(1)
              }}
            >
              Tümü <span className="badge">{durumCounts.all}</span>
            </button>
            {!isCustomer && (
              <button 
                className={`filter-btn ${filterDurum === 'taslak' ? 'active' : ''}`}
                onClick={() => {
                  setFilterDurum('taslak')
                  setPage(1)
                }}
              >
                Taslak <span className="badge">{durumCounts.taslak}</span>
              </button>
            )}
            <button 
              className={`filter-btn ${filterDurum === 'gonderildi' ? 'active' : ''}`}
              onClick={() => {
                setFilterDurum('gonderildi')
                setPage(1)
              }}
            >
              Gönderildi <span className="badge badge-warning">{durumCounts.gonderildi}</span>
            </button>
            <button 
              className={`filter-btn ${filterDurum === 'onaylandi' ? 'active' : ''}`}
              onClick={() => {
                setFilterDurum('onaylandi')
                setPage(1)
              }}
            >
              Onaylandı <span className="badge badge-success">{durumCounts.onaylandi}</span>
            </button>
            <button 
              className={`filter-btn ${filterDurum === 'reddedildi' ? 'active' : ''}`}
              onClick={() => {
                setFilterDurum('reddedildi')
                setPage(1)
              }}
            >
              Reddedildi <span className="badge badge-danger">{durumCounts.reddedildi}</span>
            </button>
          </div>
        </div>
        
        {/* Sayfa Başına Kayıt */}
        <div className="filter-group">
          <select 
            value={pageSize} 
            onChange={(e) => {
              setPageSize(Number(e.target.value))
              setPage(1)
            }}
            style={{ padding: '0.6rem', borderRadius: '8px', border: '1px solid #ddd' }}
          >
            <option value="25">25 kayıt</option>
            <option value="50">50 kayıt</option>
            <option value="100">100 kayıt</option>
            <option value="200">200 kayıt</option>
          </select>
        </div>
      </div>
      
      {/* Pagination Info */}
      {metadata.total_items > 0 && (
        <div style={{ padding: '1rem', color: '#666', fontSize: '0.9rem', backgroundColor: '#f8f9fa', borderRadius: '8px', marginBottom: '1rem' }}>
          Toplam {metadata.total_items} mutabakat bulundu (Sayfa {page} / {metadata.total_pages})
        </div>
      )}

      {/* Müşteri için bilgi mesajı */}
      {isCustomer && getCustomerMessage()}

      {/* Loading State */}
      {isLoading ? (
        <div className="table-container animate-fadeIn">
          <SkeletonLoader type="table-row" count={10} />
        </div>
      ) : !mutabakats || mutabakats.length === 0 ? (
        <div className="empty-state card animate-fadeInUp">
          <p>
            {filterDurum === '' 
              ? (isCustomer 
                  ? 'Henüz size gönderilen mutabakat bulunmuyor.'
                  : 'Henüz mutabakat belgesi bulunmuyor.')
              : `"${getDurumText(filterDurum)}" durumunda mutabakat bulunmuyor.`
            }
          </p>
          {canCreateMutabakat && filterDurum === '' && (
            <Link to="/mutabakat/new" className="btn btn-primary">
              <FaPlus /> İlk Mutabakatı Oluştur
            </Link>
          )}
        </div>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Mutabakat No</th>
                {isInternal && <th>Oluşturan</th>}
                {!isCustomer && <th>Gönderen/Alıcı</th>}
                {isCustomer && <th>Gönderen</th>}
                <th>Dönem</th>
                <th>Durum</th>
                <th>Borç</th>
                <th>Alacak</th>
                <th>Bakiye</th>
                <th>Tarih</th>
                <th>İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {mutabakats.map((mutabakat) => {
                const isSender = mutabakat.sender_id === user?.id
                const isReceiver = mutabakat.receiver_id === user?.id
                
                return (
                  <tr key={mutabakat.id} className={
                    isCustomer && mutabakat.durum === 'gonderildi' && isReceiver 
                      ? 'highlight-row' 
                      : ''
                  }>
                    <td className="font-medium">{mutabakat.mutabakat_no}</td>
                    {isInternal && (
                      <td className="sender-cell">
                        <div className="sender-info">
                          <strong>{mutabakat.sender?.company_name || mutabakat.sender?.full_name || mutabakat.sender?.username || 'Bilinmeyen'}</strong>
                          {mutabakat.sender?.full_name && mutabakat.sender?.company_name && (
                            <small>{mutabakat.sender.full_name}</small>
                          )}
                        </div>
                      </td>
                    )}
                    {!isCustomer && (
                      <td>
                        {isSender ? (
                          <span className="badge badge-info">→ {mutabakat.receiver?.company_name || mutabakat.receiver?.full_name}</span>
                        ) : (
                          <span className="badge badge-secondary">← {mutabakat.sender?.company_name || mutabakat.sender?.full_name}</span>
                        )}
                      </td>
                    )}
                    {isCustomer && (
                      <td>{mutabakat.sender?.company_name || mutabakat.sender?.full_name || 'Dino Gıda'}</td>
                    )}
                    <td>
                      {format(new Date(mutabakat.donem_baslangic), 'dd MMM yyyy', { locale: tr })} -{' '}
                      {format(new Date(mutabakat.donem_bitis), 'dd MMM yyyy', { locale: tr })}
                    </td>
                    <td>
                      <span className={`badge ${getDurumBadge(mutabakat.durum)}`}>
                        {getDurumText(mutabakat.durum)}
                        {isCustomer && mutabakat.durum === 'gonderildi' && isReceiver && ' ⏳'}
                      </span>
                    </td>
                    <td className="text-danger">{formatCurrency(mutabakat.toplam_borc)}</td>
                    <td className="text-success">{formatCurrency(mutabakat.toplam_alacak)}</td>
                    <td className={mutabakat.bakiye >= 0 ? 'text-success' : 'text-danger'}>
                      {formatCurrency(mutabakat.bakiye)}
                    </td>
                    <td>{format(new Date(mutabakat.created_at), 'dd MMM yyyy', { locale: tr })}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <Link to={`/mutabakat/${mutabakat.id}`} className="btn btn-sm btn-outline">
                          <FaEye /> {isCustomer && mutabakat.durum === 'gonderildi' && isReceiver ? 'İncele & Onayla' : 'Görüntüle'}
                        </Link>
                        {(mutabakat.durum === 'onaylandi' || mutabakat.durum === 'reddedildi') && (
                          <button
                            onClick={() => handlePreviewPDF(mutabakat)}
                            className="btn btn-sm btn-info"
                            title="PDF Önizle"
                          >
                            <FaFilePdf /> Önizle
                          </button>
                        )}
                        {mutabakat.durum === 'taslak' && !isCustomer && (
                          <LoadingButton
                            onClick={() => handleSendMutabakat(mutabakat.id, mutabakat.mutabakat_no)}
                            loading={sendingId === mutabakat.id}
                            size="small"
                            variant="success"
                            icon={<FaPaperPlane />}
                            loadingText="Gönderiliyor..."
                            style={{ whiteSpace: 'nowrap' }}
                          >
                            Gönder
                          </LoadingButton>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          
          {/* Mobile Card View */}
          <div className="mobile-card-view">
            {mutabakats.map((mutabakat) => {
              const isSender = mutabakat.sender_id === user?.id
              const isReceiver = mutabakat.receiver_id === user?.id
              
              return (
                <MutabakatMobileCard
                  key={mutabakat.id}
                  mutabakat={mutabakat}
                  isCustomer={isCustomer}
                  isReceiver={isReceiver}
                  isSender={isSender}
                  sendingId={sendingId}
                  onSend={handleSendMutabakat}
                  onPreviewPDF={handlePreviewPDF}
                  formatCurrency={formatCurrency}
                  getDurumBadge={getDurumBadge}
                  getDurumText={getDurumText}
                />
              )
            })}
          </div>
          
          {/* Pagination Controls */}
          {metadata.total_pages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem', marginTop: '2rem', flexWrap: 'wrap' }}>
              <button
                onClick={() => setPage(1)}
                disabled={page === 1}
                style={{ 
                  padding: '0.6rem 1rem', 
                  borderRadius: '8px', 
                  border: '1px solid #ddd', 
                  background: page === 1 ? '#f0f0f0' : 'white',
                  cursor: page === 1 ? 'not-allowed' : 'pointer'
                }}
              >
                İlk
              </button>
              <button
                onClick={() => setPage(p => p - 1)}
                disabled={!metadata.has_prev}
                style={{ 
                  padding: '0.6rem 1rem', 
                  borderRadius: '8px', 
                  border: '1px solid #ddd', 
                  background: !metadata.has_prev ? '#f0f0f0' : 'white',
                  cursor: !metadata.has_prev ? 'not-allowed' : 'pointer'
                }}
              >
                Önceki
              </button>
              
              <div style={{ display: 'flex', gap: '0.3rem' }}>
                {Array.from({ length: Math.min(5, metadata.total_pages) }, (_, i) => {
                  let pageNum
                  if (metadata.total_pages <= 5) {
                    pageNum = i + 1
                  } else if (page <= 3) {
                    pageNum = i + 1
                  } else if (page >= metadata.total_pages - 2) {
                    pageNum = metadata.total_pages - 4 + i
                  } else {
                    pageNum = page - 2 + i
                  }
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      style={{ 
                        padding: '0.6rem 0.9rem', 
                        borderRadius: '8px', 
                        border: '1px solid #ddd',
                        background: page === pageNum ? '#007bff' : 'white',
                        color: page === pageNum ? 'white' : 'black',
                        cursor: 'pointer',
                        fontWeight: page === pageNum ? 'bold' : 'normal'
                      }}
                    >
                      {pageNum}
                    </button>
                  )
                })}
              </div>
              
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={!metadata.has_next}
                style={{ 
                  padding: '0.6rem 1rem', 
                  borderRadius: '8px', 
                  border: '1px solid #ddd', 
                  background: !metadata.has_next ? '#f0f0f0' : 'white',
                  cursor: !metadata.has_next ? 'not-allowed' : 'pointer'
                }}
              >
                Sonraki
              </button>
              <button
                onClick={() => setPage(metadata.total_pages)}
                disabled={page === metadata.total_pages}
                style={{ 
                  padding: '0.6rem 1rem', 
                  borderRadius: '8px', 
                  border: '1px solid #ddd', 
                  background: page === metadata.total_pages ? '#f0f0f0' : 'white',
                  cursor: page === metadata.total_pages ? 'not-allowed' : 'pointer'
                }}
              >
                Son
              </button>
            </div>
          )}
        </div>
      )}

      {/* PDF Preview Modal */}
      {pdfUrl && selectedMutabakat && (
        <PDFPreviewModal
          isOpen={showPDFPreview}
          onClose={() => {
            setShowPDFPreview(false)
            if (pdfUrl) {
              window.URL.revokeObjectURL(pdfUrl)
              setPdfUrl(null)
            }
            setSelectedMutabakat(null)
          }}
          pdfUrl={pdfUrl}
          fileName={`Mutabakat_${selectedMutabakat.mutabakat_no}.pdf`}
        />
      )}
    </div>
  )
}
