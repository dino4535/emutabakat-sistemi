import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'react-toastify'
import { FaFileExcel, FaUpload, FaDownload, FaCheckCircle, FaTimesCircle, FaUsers, FaInfoCircle } from 'react-icons/fa'
import './BayiBulkUpload.css'

export default function BayiBulkUpload() {
  const [excelFile, setExcelFile] = useState(null)
  const [uploadResult, setUploadResult] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const queryClient = useQueryClient()

  // Excel yükleme - Gerçek zamanlı streaming ile
  const uploadExcelMutation = useMutation({
    mutationFn: async (file) => {
      return new Promise((resolve, reject) => {
        setIsUploading(true)
        setUploadProgress(0)
        
        const formData = new FormData()
        formData.append('file', file)
        
        const token = localStorage.getItem('token')
        
        // EventSource kullanarak streaming yapıyoruz
        // Önce dosyayı POST ile gönderiyoruz
        console.log('[UPLOAD] Excel yükleme başlatılıyor...')
        
        fetch('/api/bayi/upload-excel-stream', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'text/event-stream'
          },
          body: formData,
          cache: 'no-cache'
        }).then(async (response) => {
          console.log('[RESPONSE] Status:', response.status, 'Headers:', response.headers.get('content-type'))
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }
          
          const reader = response.body.getReader()
          const decoder = new TextDecoder()
          let buffer = ''
          let finalResult = null
          
          while (true) {
            const { done, value } = await reader.read()
            
            if (done) break
            
            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            
            // Son satırı buffer'da tut (tam olmayabilir)
            buffer = lines.pop()
            
            for (const line of lines) {
              if (line.trim().startsWith('data: ')) {
                try {
                  const jsonStr = line.slice(line.indexOf('{'))
                  const data = JSON.parse(jsonStr)
                  
                  console.log('[STREAM]', data.type, data.percent || '', data.basarili || '', '/', data.total || '')
                  
                  if (data.type === 'total') {
                    console.log(`[BAŞLANGIÇ] Toplam ${data.count} satır işlenecek`)
                  } else if (data.type === 'progress') {
                    setUploadProgress(data.percent)
                    console.log(`[İLERLEME] %${data.percent} - ${data.current}/${data.total} - Başarılı: ${data.basarili}, Başarısız: ${data.basarisiz}`)
                  } else if (data.type === 'complete') {
                    finalResult = data
                    setUploadProgress(100)
                    console.log(`[TAMAMLANDI] Toplam: ${data.toplam}, Başarılı: ${data.basarili}, Başarısız: ${data.basarisiz}`)
                  } else if (data.type === 'error') {
                    console.error('[HATA]', data.message)
                    reject(new Error(data.message))
                    setIsUploading(false)
                    return
                  }
                } catch (e) {
                  console.error('[JSON PARSE HATASI]', e, 'Line:', line)
                }
              }
            }
          }
          
          // Kısa bir süre %100'ü göster
          setTimeout(() => {
            setIsUploading(false)
            if (finalResult) {
              resolve(finalResult)
            } else {
              reject(new Error('İşlem tamamlanmadı'))
            }
          }, 800)
          
        }).catch((error) => {
          console.error('Streaming hatası:', error)
          setIsUploading(false)
          setUploadProgress(0)
          reject(error)
        })
      })
    },
    onSuccess: (data) => {
      setUploadResult(data)
      setExcelFile(null)
      
      if (data.basarili > 0) {
        toast.success(`${data.basarili} bayi başarıyla yüklendi!`)
        queryClient.invalidateQueries(['bayiler'])
      }
      
      if (data.basarisiz > 0) {
        toast.warning(`${data.basarisiz} satır hatalı`)
      }
    },
    onError: (error) => {
      console.error('Excel yükleme hatası:', error)
      
      // Timeout hatası kontrolü
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        toast.error('İşlem zaman aşımına uğradı. Lütfen daha az sayıda bayi ile tekrar deneyin veya birkaç dakika bekleyip kontrol edin.', {
          autoClose: 8000
        })
        return
      }
      
      const errorMsg = error.response?.data?.detail || error.message || 'Excel yüklenemedi'
      toast.error(errorMsg)
    }
  })

  // Template indirme
  const handleDownloadTemplate = async () => {
    try {
      const response = await axios.get('/api/bayi/download-template', { 
        responseType: 'blob' 
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'Bayi_Yukleme_Sablonu.xlsx')
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

  // Dosya seçimi
  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      // Dosya doğrulama
      const validTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']
      if (!validTypes.includes(file.type) && !file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        toast.error('Sadece Excel dosyası (.xlsx, .xls) yüklenebilir')
        return
      }
      
      // Dosya boyutu kontrolü (5 MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Dosya boyutu maksimum 5 MB olmalıdır')
        return
      }
      
      setExcelFile(file)
      setUploadResult(null)
    }
  }

  // Drag & Drop
  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    
    const file = e.dataTransfer.files[0]
    if (file) {
      const fakeEvent = { target: { files: [file] } }
      handleFileChange(fakeEvent)
    }
  }

  // Yükleme işlemi
  const handleExcelUpload = () => {
    if (!excelFile) {
      toast.error('Lütfen bir dosya seçin')
      return
    }
    
    uploadExcelMutation.mutate(excelFile)
  }

  return (
    <div className="bayi-bulk-upload">
      {/* İlerleme Overlay */}
      {isUploading && (
        <div className="upload-progress-overlay">
          <div className="upload-progress-modal">
            <div className="progress-icon-wrapper">
              <FaUpload className="progress-icon" />
            </div>
            <h2>Excel Yükleniyor...</h2>
            <p className="progress-description">
              {uploadProgress < 100 
                ? `Bayiler oluşturuluyor... (${Math.round(uploadProgress)}% tamamlandı)`
                : 'İşlem tamamlandı! ✓'}
            </p>
            
            <div className="progress-bar-wrapper">
              <div className="progress-bar">
                <div 
                  className="progress-bar-fill" 
                  style={{ width: `${uploadProgress}%` }}
                >
                  <span className="progress-bar-shimmer"></span>
                </div>
              </div>
              <div className="progress-percentage">
                %{Math.round(uploadProgress)}
              </div>
            </div>
            
            <p className="progress-note">
              Bu işlem biraz zaman alabilir. Lütfen bekleyin...
            </p>
          </div>
        </div>
      )}

      <div className="page-header">
        <div className="header-left">
          <FaUsers className="page-icon" />
          <div>
            <h1>Toplu Bayi Yükleme</h1>
            <p>Excel dosyasından toplu bayi kayıtları yükleyin</p>
          </div>
        </div>
      </div>

      {/* Bilgilendirme Banner */}
      <div className="info-banner">
        <FaInfoCircle />
        <div>
          <strong>Nasıl Çalışır?</strong>
          <p>
            1. Excel şablonunu indirin
            2. Bayi bilgilerini doldurun (VKN/TC, Bayi Kodu, Bayi Adı, Vergi Dairesi)
            3. Dosyayı yükleyin - Sistem otomatik olarak VKN'ye göre kullanıcı hesapları oluşturur
          </p>
        </div>
      </div>

      {/* Template İndirme */}
      <div className="template-section">
        <div className="section-header">
          <h2>
            <FaDownload />
            1. Excel Şablonu
          </h2>
        </div>
        <div className="template-card">
          <FaFileExcel className="template-icon" />
          <div className="template-info">
            <h3>Bayi Yükleme Şablonu</h3>
            <p>Örnek veriler ve kullanım kılavuzu içerir</p>
            <ul className="template-features">
              <li>✓ 5 örnek bayi kaydı</li>
              <li>✓ Detaylı kullanım kılavuzu</li>
              <li>✓ Kolon açıklamaları</li>
              <li>✓ Maks. 5.000 satır</li>
            </ul>
          </div>
          <button 
            onClick={handleDownloadTemplate} 
            className="btn btn-primary"
          >
            <FaDownload /> Şablonu İndir
          </button>
        </div>
      </div>

      {/* Dosya Yükleme */}
      <div className="upload-section">
        <div className="section-header">
          <h2>
            <FaUpload />
            2. Excel Dosyasını Yükle
          </h2>
        </div>
        
        <div 
          className={`upload-dropzone ${isDragging ? 'dragging' : ''} ${excelFile ? 'has-file' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !excelFile && document.getElementById('excel-file-input').click()}
        >
          {excelFile ? (
            <div className="file-selected">
              <FaFileExcel className="file-icon" />
              <div className="file-info">
                <h3>{excelFile.name}</h3>
                <p>{(excelFile.size / 1024).toFixed(2)} KB</p>
              </div>
              <button 
                onClick={(e) => {
                  e.stopPropagation()
                  setExcelFile(null)
                  setUploadResult(null)
                }} 
                className="btn btn-secondary btn-sm"
              >
                Değiştir
              </button>
            </div>
          ) : (
            <div className="dropzone-placeholder">
              <FaUpload className="upload-icon" />
              <h3>Excel dosyasını sürükleyip bırakın</h3>
              <p>veya tıklayarak seçin</p>
              <span className="file-requirements">
                Maksimum 5.000 satır • 5 MB • .xlsx, .xls
              </span>
            </div>
          )}
          <input 
            id="excel-file-input"
            type="file" 
            accept=".xlsx,.xls" 
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
        </div>

        {excelFile && (
          <button 
            onClick={handleExcelUpload} 
            className="btn btn-success btn-lg"
            disabled={uploadExcelMutation.isPending}
          >
            {uploadExcelMutation.isPending ? (
              <>
                <span className="spinner"></span> Yükleniyor...
              </>
            ) : (
              <>
                <FaUpload /> Yüklemeyi Başlat
              </>
            )}
          </button>
        )}
      </div>

      {/* Yükleme Sonuçları */}
      {uploadResult && (
        <div className="upload-result">
          <h2>Yükleme Sonuçları</h2>
          
          <div className="result-summary">
            <div className="result-item total">
              <FaFileExcel />
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
                <span className="result-label">Hatalı</span>
              </div>
            </div>
          </div>

          {/* Başarılı Yüklemeler */}
          {uploadResult.olusturulan_bayiler?.length > 0 && (
            <div className="result-section success-list">
              <h3>
                <FaCheckCircle /> Başarılı Yüklemeler ({uploadResult.olusturulan_bayiler.length})
              </h3>
              <div className="result-table-wrapper">
                <table className="result-table">
                  <thead>
                    <tr>
                      <th>Satır</th>
                      <th>VKN/TC</th>
                      <th>Bayi Kodu</th>
                      <th>Bayi Adı</th>
                    </tr>
                  </thead>
                  <tbody>
                    {uploadResult.olusturulan_bayiler.slice(0, 10).map((bayi) => (
                      <tr key={bayi.satir}>
                        <td>{bayi.satir}</td>
                        <td><code>{bayi.vkn_tckn}</code></td>
                        <td><code>{bayi.bayi_kodu}</code></td>
                        <td>{bayi.bayi_adi}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {uploadResult.olusturulan_bayiler.length > 10 && (
                  <p className="table-note">
                    İlk 10 kayıt gösteriliyor. Toplam {uploadResult.olusturulan_bayiler.length} kayıt yüklendi.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Hatalar */}
          {uploadResult.hatalar?.length > 0 && (
            <div className="result-section error-list">
              <h3>
                <FaTimesCircle /> Hatalar ({uploadResult.hatalar.length})
              </h3>
              <div className="error-items">
                {uploadResult.hatalar.map((hata, index) => (
                  <div key={index} className="error-item">
                    <div className="error-header">
                      <span className="error-row">Satır {hata.satir}</span>
                      <span className="error-message">{hata.hata}</span>
                    </div>
                    {hata.veri && (
                      <div className="error-data">
                        <code>
                          {hata.veri.bayi_kodu && `Bayi Kodu: ${hata.veri.bayi_kodu}`}
                          {hata.veri.vkn_tckn && ` | VKN: ${hata.veri.vkn_tckn}`}
                          {hata.veri.bayi_adi && ` | Bayi Adı: ${hata.veri.bayi_adi}`}
                        </code>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

