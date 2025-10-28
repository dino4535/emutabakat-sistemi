import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'react-toastify'
import { useNavigate } from 'react-router-dom'
import { FaUsers, FaFileAlt, FaUpload, FaDownload, FaFileExcel, FaCheckCircle, FaTimesCircle } from 'react-icons/fa'
import ProgressBar from '../components/ProgressBar'
import LoadingButton from '../components/LoadingButton'
import SkeletonLoader from '../components/SkeletonLoader'
import './BulkMutabakat.css'

export default function BulkMutabakat() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [activeTab, setActiveTab] = useState('manuel') // 'manuel' veya 'excel'
  const [selectedCustomers, setSelectedCustomers] = useState([])
  const [donemBaslangic, setDonemBaslangic] = useState('')
  const [donemBitis, setDonemBitis] = useState('')
  const [excelFile, setExcelFile] = useState(null)
  const [uploadResult, setUploadResult] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)

  // Müşterileri getir
  const { data: customers, isLoading } = useQuery({
    queryKey: ['bulk-customers'],
    queryFn: async () => {
      const response = await axios.get('/api/bulk-mutabakat/customers')
      return response.data
    }
  })

  // Toplu mutabakat oluştur
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await axios.post('/api/bulk-mutabakat/create-multiple', null, {
        params: data
      })
      return response.data
    },
    onSuccess: (data) => {
      toast.success(`${data.length} adet mutabakat oluşturuldu!`)
      queryClient.invalidateQueries(['mutabakats'])
      navigate('/mutabakat')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Toplu mutabakat oluşturulamadı')
    }
  })

  // Excel yükleme
  const uploadExcelMutation = useMutation({
    mutationFn: async (file) => {
      setIsUploading(true)
      setUploadProgress(0)
      
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await axios.post('/api/bulk-mutabakat/upload-excel', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          setUploadProgress(percentCompleted)
        }
      })
      return response.data
    },
    onSuccess: (data) => {
      setUploadResult(data)
      setExcelFile(null)
      setIsUploading(false)
      setUploadProgress(0)
      
      if (data.basarili > 0) {
        toast.success(`${data.basarili} mutabakat TASLAK olarak kaydedildi! Mutabakat listesinden kontrol edip gönderebilirsiniz.`)
        queryClient.invalidateQueries(['mutabakats'])
      }
      
      if (data.basarisiz > 0) {
        toast.warning(`${data.basarisiz} satır hatalı`)
      }
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Excel yüklenemedi')
      setUploadResult(null)
      setIsUploading(false)
      setUploadProgress(0)
    }
  })

  // Template indirme
  const handleDownloadTemplate = async () => {
    try {
      const response = await axios.get('/api/bulk-mutabakat/download-template', {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'Mutabakat_Sablonu.xlsx')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
      toast.success('Template indirildi')
    } catch (error) {
      console.error('Template indirme hatası:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Template indirilemedi'
      toast.error(errorMsg)
    }
  }

  const handleCustomerToggle = (customerId) => {
    setSelectedCustomers(prev =>
      prev.includes(customerId)
        ? prev.filter(id => id !== customerId)
        : [...prev, customerId]
    )
  }

  const handleSelectAll = () => {
    if (selectedCustomers.length === customers?.length) {
      setSelectedCustomers([])
    } else {
      setSelectedCustomers(customers?.map(c => c.id) || [])
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (selectedCustomers.length === 0) {
      toast.error('Lütfen en az bir müşteri seçin')
      return
    }

    if (!donemBaslangic || !donemBitis) {
      toast.error('Lütfen dönem tarihlerini girin')
      return
    }

    createMutation.mutate({
      receivers: selectedCustomers,
      donem_baslangic: new Date(donemBaslangic).toISOString(),
      donem_bitis: new Date(donemBitis).toISOString()
    })
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        toast.error('Lütfen Excel dosyası seçiniz (.xlsx veya .xls)')
        return
      }
      
      if (file.size > 5 * 1024 * 1024) { // 5 MB
        toast.error('Dosya boyutu maksimum 5 MB olmalıdır')
        return
      }
      
      setExcelFile(file)
      setUploadResult(null) // Önceki sonuçları temizle
    }
  }

  const handleExcelUpload = () => {
    if (!excelFile) {
      toast.error('Lütfen bir Excel dosyası seçiniz')
      return
    }
    
    uploadExcelMutation.mutate(excelFile)
  }

  if (isLoading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="bulk-mutabakat">
      <div className="bulk-header">
        <div>
          <h1>Toplu Mutabakat Oluştur</h1>
          <p>Birden fazla müşteri için aynı anda mutabakat oluşturun</p>
        </div>
      </div>

      {/* Tab Buttons */}
      <div className="tab-buttons">
        <button
          type="button"
          className={`tab-button ${activeTab === 'manuel' ? 'active' : ''}`}
          onClick={() => setActiveTab('manuel')}
        >
          <FaUsers /> Manuel Seçim
        </button>
        <button
          type="button"
          className={`tab-button ${activeTab === 'excel' ? 'active' : ''}`}
          onClick={() => setActiveTab('excel')}
        >
          <FaFileExcel /> Excel'den Yükle
        </button>
      </div>

      {/* Manuel Seçim Tab */}
      {activeTab === 'manuel' && (
        <form onSubmit={handleSubmit}>
        <div className="bulk-content">
          {/* Dönem Seçimi */}
          <div className="card">
            <h3><FaFileAlt /> Dönem Bilgileri</h3>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Dönem Başlangıç *</label>
                <input
                  type="date"
                  className="form-input"
                  value={donemBaslangic}
                  onChange={(e) => setDonemBaslangic(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Dönem Bitiş *</label>
                <input
                  type="date"
                  className="form-input"
                  value={donemBitis}
                  onChange={(e) => setDonemBitis(e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          {/* Müşteri Seçimi */}
          <div className="card">
            <div className="customer-header">
              <h3><FaUsers /> Müşteri Seçimi</h3>
              <div className="customer-actions">
                <button
                  type="button"
                  onClick={handleSelectAll}
                  className="btn btn-outline btn-sm"
                >
                  {selectedCustomers.length === customers?.length ? 'Tümünü Kaldır' : 'Tümünü Seç'}
                </button>
                <span className="selected-count">
                  {selectedCustomers.length} / {customers?.length || 0} seçili
                </span>
              </div>
            </div>

            {isLoading ? (
              <div className="customer-list animate-fadeIn">
                <SkeletonLoader type="list-item" count={5} />
              </div>
            ) : !customers || customers.length === 0 ? (
              <div className="empty-state">
                <p>Henüz müşteri bulunmuyor.</p>
              </div>
            ) : (
              <div className="customer-list animate-fadeInUp">
                {customers.map((customer) => (
                  <div
                    key={customer.id}
                    className={`customer-item ${selectedCustomers.includes(customer.id) ? 'selected' : ''}`}
                    onClick={() => handleCustomerToggle(customer.id)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedCustomers.includes(customer.id)}
                      onChange={() => {}}
                    />
                    <div className="customer-info">
                      <h4>{customer.company_name || customer.full_name}</h4>
                      <p>{customer.email}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Netsis Entegrasyonu (Gelecek) */}
          <div className="card netsis-card">
            <h3><FaUpload /> Netsis Entegrasyonu</h3>
            <p className="coming-soon">
              Netsis'ten cari ekstre çekerek otomatik mutabakat oluşturma özelliği yakında eklenecek.
            </p>
            <button type="button" className="btn btn-secondary" disabled>
              <FaUpload /> Netsis'ten Aktar (Yakında)
            </button>
          </div>
        </div>

        {/* Alt Butonlar */}
        <div className="bulk-actions">
          <button
            type="button"
            onClick={() => navigate('/mutabakat')}
            className="btn btn-secondary"
          >
            İptal
          </button>
          <LoadingButton
            type="submit"
            loading={createMutation.isPending}
            disabled={selectedCustomers.length === 0}
            variant="primary"
            icon={<FaFileAlt />}
            loadingText="Oluşturuluyor..."
            size="large"
          >
            {selectedCustomers.length} Müşteri İçin Oluştur
          </LoadingButton>
        </div>
      </form>
      )}

      {/* Excel Yükleme Tab */}
      {activeTab === 'excel' && (
        <div className="excel-upload-section">
          <div className="card">
            <h3><FaFileExcel /> Excel Dosyasından Toplu Yükleme</h3>
            <p className="info-text">
              Excel şablonunu indirip doldurun, ardından sisteme yükleyin. Müşteriler otomatik olarak oluşturulacak ve mutabakatlar gönderilecektir.
            </p>

            {/* Template İndirme */}
            <div className="template-download">
              <div className="template-info">
                <FaDownload />
                <div>
                  <h4>1. Excel Şablonunu İndirin</h4>
                  <p>İlk olarak Excel şablonunu indirip doldurunuz</p>
                </div>
              </div>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleDownloadTemplate}
              >
                <FaDownload /> Şablon İndir
              </button>
            </div>

            {/* Dosya Yükleme */}
            <div className="file-upload-section">
              <div className="upload-info">
                <FaUpload />
                <div>
                  <h4>2. Doldurduğunuz Dosyayı Yükleyin</h4>
                  <p>Maksimum 1.000 satır, 5 MB dosya boyutu</p>
                </div>
              </div>
              
              <div className="file-upload-box">
                <input
                  type="file"
                  id="excel-file"
                  accept=".xlsx,.xls"
                  onChange={handleFileChange}
                  className="file-input"
                />
                <label htmlFor="excel-file" className="file-label">
                  {excelFile ? (
                    <>
                      <FaFileExcel className="file-icon" />
                      <span>{excelFile.name}</span>
                      <small>({(excelFile.size / 1024).toFixed(2)} KB)</small>
                    </>
                  ) : (
                    <>
                      <FaUpload className="upload-icon" />
                      <span>Excel dosyası seçmek için tıklayın</span>
                      <small>veya sürükle bırak</small>
                    </>
                  )}
                </label>
              </div>

              <LoadingButton
                type="button"
                onClick={handleExcelUpload}
                loading={uploadExcelMutation.isPending}
                disabled={!excelFile}
                variant="primary"
                icon={<FaUpload />}
                loadingText="Yükleniyor..."
                size="large"
              >
                Yükle ve İşle
              </LoadingButton>
            </div>

            {/* Upload Progress */}
            {isUploading && uploadProgress > 0 && (
              <div style={{ marginTop: '20px' }}>
                <ProgressBar 
                  progress={uploadProgress}
                  color="primary"
                  striped
                  animated
                  label="Excel yükleniyor..."
                  showPercentage
                />
              </div>
            )}

            {/* Yükleme Sonuçları */}
            {uploadResult && (
              <div className="upload-result">
                <h3>Yükleme Sonuçları</h3>
                
                {uploadResult.basarili > 0 && (
                  <div className="info-banner">
                    <FaCheckCircle style={{ color: '#48bb78', fontSize: '20px' }} />
                    <div>
                      <strong>Mutabakatlar TASLAK olarak kaydedildi!</strong>
                      <p>Mutabakat listesinden kontrol edip, "Gönder" butonuyla müşterilerinize gönderebilirsiniz.</p>
                    </div>
                  </div>
                )}
                
                <div className="result-summary">
                  <div className="result-item total">
                    <FaFileAlt />
                    <div>
                      <span className="result-number">{uploadResult.toplam}</span>
                      <span className="result-label">Toplam Satır</span>
                    </div>
                  </div>
                  <div className="result-item success">
                    <FaCheckCircle />
                    <div>
                      <span className="result-number">{uploadResult.basarili}</span>
                      <span className="result-label">Başarılı</span>
                    </div>
                  </div>
                  <div className="result-item error">
                    <FaTimesCircle />
                    <div>
                      <span className="result-number">{uploadResult.basarisiz}</span>
                      <span className="result-label">Başarısız</span>
                    </div>
                  </div>
                </div>

                {/* Başarılı Mutabakatlar */}
                {uploadResult.olusturulan_mutabakatlar?.length > 0 && (
                  <div className="success-list">
                    <h4><FaCheckCircle /> Oluşturulan Mutabakatlar</h4>
                    <div className="success-items">
                      {uploadResult.olusturulan_mutabakatlar.map((item, index) => (
                        <div key={index} className="success-item">
                          <span className="mutabakat-no">{item.mutabakat_no}</span>
                          <span className="musteri-adi">{item.musteri}</span>
                          <span className="bakiye">
                            {item.bakiye >= 0 ? 'Borç: ' : 'Alacak: '}
                            {Math.abs(item.bakiye).toFixed(2)} ₺
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Hatalar */}
                {uploadResult.hatalar?.length > 0 && (
                  <div className="error-list">
                    <h4><FaTimesCircle /> Hatalar</h4>
                    <div className="error-items">
                      {uploadResult.hatalar.map((error, index) => (
                        <div key={index} className="error-item">
                          <span className="error-row">Satır {error.satir}</span>
                          <span className="error-customer">{error.musteri}</span>
                          <span className="error-message">{error.hata}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="result-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setUploadResult(null)}
                  >
                    Yeni Yükleme
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => navigate('/mutabakat')}
                  >
                    Mutabakatlara Git
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

