import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { FaBuilding, FaPlus, FaEdit, FaTrash, FaTimes, FaSave, FaUsers, FaFileAlt } from 'react-icons/fa'
import axios from 'axios'
import SkeletonLoader from '../components/SkeletonLoader'
import LoadingButton from '../components/LoadingButton'
import './CompanyManagement.css'

export default function CompanyManagement() {
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [editingCompany, setEditingCompany] = useState(null)
  const [formData, setFormData] = useState({
    vkn: '',
    company_name: '',
    full_company_name: '',
    tax_office: '',
    address: '',
    phone: '',
    email: '',
    website: '',
    logo_path: '',
    primary_color: '#667eea',
    secondary_color: '#764ba2',
    notification_email: '',  // Mutabakat bildirimleri için
    sms_enabled: true,
    sms_provider: 'netgsm',
    sms_header: '',
    sms_username: '',
    sms_password: '',
    kvkk_policy_text: '',
    kvkk_policy_version: '1.0',
    customer_notice_text: '',
    customer_notice_version: '1.0',
    data_retention_policy_text: '',
    data_retention_version: '1.0',
    system_consent_text: '',
    system_consent_version: '1.0'
  })

  useEffect(() => {
    fetchCompanies()
  }, [])

  const fetchCompanies = async () => {
    try {
      const response = await axios.get('/api/admin/companies/')
      setCompanies(response.data)
    } catch (error) {
      toast.error('Şirketler yüklenemedi')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleOpenModal = (company = null) => {
    if (company) {
      setEditingCompany(company)
      setFormData({
        vkn: company.vkn,
        company_name: company.company_name,
        full_company_name: company.full_company_name || '',
        tax_office: company.tax_office || '',
        address: company.address || '',
        phone: company.phone || '',
        email: company.email || '',
        website: company.website || '',
        logo_path: company.logo_path || '',
        primary_color: company.primary_color || '#667eea',
        secondary_color: company.secondary_color || '#764ba2',
        notification_email: company.notification_email || '',  // Mutabakat bildirimleri
        sms_enabled: company.sms_enabled,
        sms_provider: company.sms_provider || 'netgsm',
        sms_header: company.sms_header || '',
        sms_username: company.sms_username || '',
        sms_password: '', // Güvenlik: mevcut şifre gösterilmez
        kvkk_policy_text: company.kvkk_policy_text || '',
        kvkk_policy_version: company.kvkk_policy_version || '1.0',
        customer_notice_text: company.customer_notice_text || '',
        customer_notice_version: company.customer_notice_version || '1.0',
        data_retention_policy_text: company.data_retention_policy_text || '',
        data_retention_version: company.data_retention_version || '1.0',
        system_consent_text: company.system_consent_text || '',
        system_consent_version: company.system_consent_version || '1.0'
      })
    } else {
      setEditingCompany(null)
      setFormData({
        vkn: '',
        company_name: '',
        full_company_name: '',
        tax_office: '',
        address: '',
        phone: '',
        email: '',
        website: '',
        logo_path: '',
        primary_color: '#667eea',
        secondary_color: '#764ba2',
        notification_email: '',  // Mutabakat bildirimleri
        sms_enabled: true,
        sms_provider: 'netgsm',
        sms_header: '',
        sms_username: '',
        sms_password: '',
        kvkk_policy_text: '',
        kvkk_policy_version: '1.0',
        customer_notice_text: '',
        customer_notice_version: '1.0',
        data_retention_policy_text: '',
        data_retention_version: '1.0',
        system_consent_text: '',
        system_consent_version: '1.0'
      })
    }
    setShowModal(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    
    try {
      if (editingCompany) {
        // Güncelleme - boş şifre gönderme (değiştirilmemişse)
        const updateData = { ...formData }
        if (!updateData.sms_password || updateData.sms_password === '') {
          delete updateData.sms_password
        }
        await axios.put(`/api/admin/companies/${editingCompany.id}`, updateData)
        toast.success('Şirket güncellendi')
      } else {
        // Yeni oluşturma
        await axios.post('/api/admin/companies/', formData)
        toast.success('Şirket oluşturuldu')
      }
      
      setShowModal(false)
      fetchCompanies()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'İşlem başarısız')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (company) => {
    if (!window.confirm(`"${company.company_name}" şirketini silmek istediğinize emin misiniz?\n\n⚠️ Bu işlem geri alınamaz!`)) {
      return
    }

    try {
      await axios.delete(`/api/admin/companies/${company.id}`)
      toast.success('Şirket silindi')
      fetchCompanies()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Silme başarısız')
    }
  }

  return (
    <div className="company-management">
      <div className="page-header">
        <div className="header-content">
          <div className="header-left">
            <FaBuilding className="header-icon" />
            <div>
              <h1>Şirket Yönetimi</h1>
              <p>{companies.length} şirket kayıtlı</p>
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => handleOpenModal()}>
            <FaPlus /> Yeni Şirket Ekle
          </button>
        </div>
      </div>

      {loading ? (
        <div className="companies-grid animate-fadeIn">
          <SkeletonLoader type="card" count={3} height="300px" />
        </div>
      ) : (
        <div className="companies-grid animate-fadeInUp">
          {companies.map(company => (
          <div key={company.id} className={`company-card ${!company.is_active ? 'inactive' : ''}`}>
            <div className="company-card-header">
              <div className="company-logo">
                <FaBuilding style={{ color: company.primary_color }} />
              </div>
              <div className="company-status">
                {company.is_active ? (
                  <span className="badge badge-success">Aktif</span>
                ) : (
                  <span className="badge badge-danger">Pasif</span>
                )}
              </div>
            </div>

            <div className="company-card-body">
              <h3>{company.company_name}</h3>
              <p className="company-vkn">VKN: {company.vkn}</p>
              {company.full_company_name && (
                <p className="company-full-name">{company.full_company_name}</p>
              )}

              <div className="company-stats">
                <div className="stat">
                  <FaUsers />
                  <span>{company.user_count} Kullanıcı</span>
                </div>
                <div className="stat">
                  <FaFileAlt />
                  <span>{company.mutabakat_count} Mutabakat</span>
                </div>
              </div>

              {company.sms_enabled && (
                <div className="company-sms-badge">
                  📱 SMS: {company.sms_header || 'Aktif'}
                </div>
              )}
            </div>

            <div className="company-card-footer">
              <button 
                className="btn btn-sm btn-secondary"
                onClick={() => handleOpenModal(company)}
              >
                <FaEdit /> Düzenle
              </button>
              <button 
                className="btn btn-sm btn-danger"
                onClick={() => handleDelete(company)}
              >
                <FaTrash /> Sil
              </button>
            </div>
          </div>
        ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content company-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                <FaBuilding /> {editingCompany ? 'Şirket Düzenle' : 'Yeni Şirket Ekle'}
              </h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                <FaTimes />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-section">
                  <h4>📋 Temel Bilgiler</h4>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>VKN *</label>
                      <input
                        type="text"
                        value={formData.vkn}
                        onChange={(e) => setFormData({...formData, vkn: e.target.value})}
                        required
                        disabled={editingCompany} // VKN değiştirilemez
                        placeholder="1234567890"
                      />
                    </div>

                    <div className="form-group">
                      <label>Şirket Adı *</label>
                      <input
                        type="text"
                        value={formData.company_name}
                        onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                        required
                        placeholder="Dino Gıda"
                      />
                    </div>

                    <div className="form-group full-width">
                      <label>Tam Ünvan</label>
                      <input
                        type="text"
                        value={formData.full_company_name}
                        onChange={(e) => setFormData({...formData, full_company_name: e.target.value})}
                        placeholder="Hüseyin ve İbrahim Kaplan Dino Gıda San. Tic. Ltd. Şti."
                      />
                    </div>

                    <div className="form-group">
                      <label>Vergi Dairesi</label>
                      <input
                        type="text"
                        value={formData.tax_office}
                        onChange={(e) => setFormData({...formData, tax_office: e.target.value})}
                        placeholder="Menderes"
                      />
                    </div>

                    <div className="form-group">
                      <label>Telefon</label>
                      <input
                        type="text"
                        value={formData.phone}
                        onChange={(e) => setFormData({...formData, phone: e.target.value})}
                        placeholder="0850 220 45 66"
                      />
                    </div>

                    <div className="form-group">
                      <label>E-posta</label>
                      <input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({...formData, email: e.target.value})}
                        placeholder="info@example.com"
                      />
                    </div>

                    <div className="form-group">
                      <label>Website</label>
                      <input
                        type="text"
                        value={formData.website}
                        onChange={(e) => setFormData({...formData, website: e.target.value})}
                        placeholder="www.example.com"
                      />
                    </div>

                    <div className="form-group full-width">
                      <label>Adres</label>
                      <textarea
                        value={formData.address}
                        onChange={(e) => setFormData({...formData, address: e.target.value})}
                        rows="2"
                        placeholder="Tam adres..."
                      />
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <h4>🎨 Branding</h4>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Logo Yolu</label>
                      <input
                        type="text"
                        value={formData.logo_path}
                        onChange={(e) => setFormData({...formData, logo_path: e.target.value})}
                        placeholder="frontend/public/logos/company-logo.png"
                      />
                    </div>

                    <div className="form-group">
                      <label>Ana Renk</label>
                      <input
                        type="color"
                        value={formData.primary_color}
                        onChange={(e) => setFormData({...formData, primary_color: e.target.value})}
                      />
                    </div>

                    <div className="form-group">
                      <label>İkinci Renk</label>
                      <input
                        type="color"
                        value={formData.secondary_color}
                        onChange={(e) => setFormData({...formData, secondary_color: e.target.value})}
                      />
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <h4>📧 Bildirim Ayarları</h4>
                  <div className="form-grid">
                    <div className="form-group full-width">
                      <label>Mutabakat Bildirimleri Email Adresi</label>
                      <input
                        type="email"
                        value={formData.notification_email}
                        onChange={(e) => setFormData({...formData, notification_email: e.target.value})}
                        placeholder="mutabakat@example.com"
                      />
                      <small style={{color: '#666', fontSize: '0.85em'}}>
                        📬 Mutabakat onay/red bildirimleri bu adrese gönderilecektir
                      </small>
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <h4>📱 SMS Ayarları</h4>
                  <div className="form-grid">
                    <div className="form-group">
                      <label className="checkbox-label">
                        <input
                          type="checkbox"
                          checked={formData.sms_enabled}
                          onChange={(e) => setFormData({...formData, sms_enabled: e.target.checked})}
                        />
                        SMS Etkin
                      </label>
                    </div>

                    {formData.sms_enabled && (
                      <>
                        <div className="form-group">
                          <label>SMS Başlığı</label>
                          <input
                            type="text"
                            value={formData.sms_header}
                            onChange={(e) => setFormData({...formData, sms_header: e.target.value})}
                            placeholder="DINOGIDA"
                            maxLength="11"
                          />
                        </div>

                        <div className="form-group">
                          <label>SMS Username</label>
                          <input
                            type="text"
                            value={formData.sms_username}
                            onChange={(e) => setFormData({...formData, sms_username: e.target.value})}
                            placeholder="sms_username"
                          />
                        </div>

                        <div className="form-group">
                          <label>SMS Password</label>
                          <input
                            type="password"
                            value={formData.sms_password}
                            onChange={(e) => setFormData({...formData, sms_password: e.target.value})}
                            placeholder={editingCompany ? "(değiştirmek için yazın)" : "password"}
                          />
                        </div>
                      </>
                    )}
                  </div>
                </div>

                <div className="form-section">
                  <h4>📄 KVKK Metinleri</h4>
                  <p style={{fontSize: '0.9em', color: '#666', marginBottom: '15px'}}>
                    Şirket bazlı KVKK metinlerini buradan düzenleyebilirsiniz. Boş bırakırsanız varsayılan metinler kullanılır.
                  </p>
                  
                  <div className="form-group full-width">
                    <label>1. KVKK Politikası</label>
                    <textarea
                      value={formData.kvkk_policy_text}
                      onChange={(e) => setFormData({...formData, kvkk_policy_text: e.target.value})}
                      rows="6"
                      placeholder="Kişisel Verilerin Korunması ve İşlenmesi Politikası metni..."
                      style={{fontFamily: 'monospace', fontSize: '0.85em'}}
                    />
                    <small style={{color: '#999'}}>
                      {formData.kvkk_policy_text.length} karakter
                    </small>
                  </div>

                  <div className="form-group full-width">
                    <label>2. Müşteri Aydınlatma Metni</label>
                    <textarea
                      value={formData.customer_notice_text}
                      onChange={(e) => setFormData({...formData, customer_notice_text: e.target.value})}
                      rows="6"
                      placeholder="Müşteri Aydınlatma Metni..."
                      style={{fontFamily: 'monospace', fontSize: '0.85em'}}
                    />
                    <small style={{color: '#999'}}>
                      {formData.customer_notice_text.length} karakter
                    </small>
                  </div>

                  <div className="form-group full-width">
                    <label>3. Veri Saklama ve İmha Politikası</label>
                    <textarea
                      value={formData.data_retention_policy_text}
                      onChange={(e) => setFormData({...formData, data_retention_policy_text: e.target.value})}
                      rows="6"
                      placeholder="Veri Saklama ve İmha Politikası metni..."
                      style={{fontFamily: 'monospace', fontSize: '0.85em'}}
                    />
                    <small style={{color: '#999'}}>
                      {formData.data_retention_policy_text.length} karakter
                    </small>
                  </div>

                  <div className="form-group full-width">
                    <label>4. E-Mutabakat Sistemi Kullanım Onayı</label>
                    <textarea
                      value={formData.system_consent_text}
                      onChange={(e) => setFormData({...formData, system_consent_text: e.target.value})}
                      rows="6"
                      placeholder="E-Mutabakat Sistemi Kullanım Onayı ve Bilgilendirme metni..."
                      style={{fontFamily: 'monospace', fontSize: '0.85em'}}
                    />
                    <small style={{color: '#999'}}>
                      {formData.system_consent_text.length} karakter
                    </small>
                  </div>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  <FaTimes /> İptal
                </button>
                <LoadingButton
                  type="submit"
                  loading={saving}
                  variant="primary"
                  icon={<FaSave />}
                  loadingText={editingCompany ? 'Güncelleniyor...' : 'Oluşturuluyor...'}
                >
                  {editingCompany ? 'Güncelle' : 'Oluştur'}
                </LoadingButton>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

