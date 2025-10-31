import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'react-toastify'
import { 
  FaUsers, FaUserPlus, FaEdit, FaTrash, FaFileExcel, 
  FaDownload, FaUpload, FaCheckCircle, FaTimesCircle,
  FaEye, FaEyeSlash, FaTimes, FaSave, FaBan, FaToggleOn,
  FaShieldAlt
} from 'react-icons/fa'
import SkeletonLoader from '../components/SkeletonLoader'
import LoadingButton from '../components/LoadingButton'
import ProgressBar from '../components/ProgressBar'
import FilterPanel, { FilterGroup, FilterItem } from '../components/FilterPanel'
import DateRangePicker from '../components/DateRangePicker'
import FilterBadges from '../components/FilterBadges'
import './UserManagement.css'

export default function UserManagement() {
  const queryClient = useQueryClient()
  
  const [activeTab, setActiveTab] = useState('list') // 'list', 'add', 'excel'
  const [selectedUser, setSelectedUser] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [excelFile, setExcelFile] = useState(null)
  const [uploadResult, setUploadResult] = useState(null)
  const [showKVKKModal, setShowKVKKModal] = useState(false)
  const [selectedUserForKVKK, setSelectedUserForKVKK] = useState(null)
  const [kvkkConsent, setKvkkConsent] = useState(null)
  const [kvkkLoading, setKvkkLoading] = useState(false)
  const [showDeleteKVKKConfirm, setShowDeleteKVKKConfirm] = useState(false)
  
  // Pagination state
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [activeFilter, setActiveFilter] = useState('')
  
  // Advanced Filter States
  const [filterPanelOpen, setFilterPanelOpen] = useState(false)
  const [dateStart, setDateStart] = useState('')
  const [dateEnd, setDateEnd] = useState('')
  const [selectedCompany, setSelectedCompany] = useState('')
  const [selectedRoles, setSelectedRoles] = useState([]) // Multi-select roles
  
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    company_name: '',
    tax_number: '',
    phone: '',
    address: '',
    role: 'musteri',
    bayi_kodu: ''
  })

  // Kullanıcıları getir (paginated)
  const { data: usersData, isLoading } = useQuery({
    queryKey: ['users', page, pageSize, searchTerm, roleFilter, activeFilter, dateStart, dateEnd, selectedCompany, selectedRoles],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      
      if (searchTerm) params.append('search', searchTerm)
      if (roleFilter) params.append('role', roleFilter)
      if (activeFilter !== '') params.append('is_active', activeFilter)
      if (dateStart) params.append('date_start', dateStart)
      if (dateEnd) params.append('date_end', dateEnd)
      if (selectedCompany) params.append('company', selectedCompany)
      if (selectedRoles.length > 0) params.append('roles', selectedRoles.join(','))
      
      const response = await axios.get(`/api/auth/users?${params.toString()}`)
      console.log('📊 Users API Response:', response.data)
      return response.data
    }
  })
  
  const users = usersData?.items || []
  const metadata = usersData?.metadata || { total_pages: 0, total_items: 0, has_next: false, has_prev: false }
  
  console.log('👥 Users Data:', { usersData, users, metadata })

  // Kullanıcı oluştur
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const payload = { ...data }
      // Backend beklenen alan adı: vkn_tckn
      if (payload.tax_number !== undefined) {
        payload.vkn_tckn = payload.tax_number
        delete payload.tax_number
      }
      const response = await axios.post('/api/auth/users', payload)
      return response.data
    },
    onSuccess: () => {
      toast.success('Kullanıcı başarıyla oluşturuldu')
      queryClient.invalidateQueries(['users'])
      resetForm()
      setActiveTab('list')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Kullanıcı oluşturulamadı')
    }
  })

  // Kullanıcı güncelle
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const payload = { ...data }
      // Backend beklenen alan adı: vkn_tckn
      if (payload.tax_number !== undefined) {
        payload.vkn_tckn = payload.tax_number
        delete payload.tax_number
      }
      const response = await axios.put(`/api/auth/users/${id}`, payload)
      return response.data
    },
    onSuccess: () => {
      toast.success('Kullanıcı başarıyla güncellendi')
      queryClient.invalidateQueries(['users'])
      setShowModal(false)
      setSelectedUser(null)
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Kullanıcı güncellenemedi')
    }
  })

  // Kullanıcı sil
  const deleteMutation = useMutation({
    mutationFn: async (userId) => {
      await axios.delete(`/api/auth/users/${userId}`)
    },
    onSuccess: () => {
      toast.success('Kullanıcı kalıcı olarak silindi')
      queryClient.invalidateQueries(['users'])
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Kullanıcı silinemedi')
    }
  })

  // Kullanıcıyı aktif/pasif yap
  const toggleActiveMutation = useMutation({
    mutationFn: async (userId) => {
      const response = await axios.put(`/api/auth/users/${userId}/toggle-active`)
      return response.data
    },
    onSuccess: (data) => {
      const status = data.is_active ? 'aktif' : 'pasif'
      toast.success(`Kullanıcı ${status} yapıldı`)
      queryClient.invalidateQueries(['users'])
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'İşlem başarısız')
    }
  })

  // Excel yükleme
  const uploadExcelMutation = useMutation({
    mutationFn: async (file) => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await axios.post('/api/auth/upload-users-excel', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 30000
      })
      return response.data
    },
    onSuccess: (data) => {
      setUploadResult(data)
      setExcelFile(null)
      
      // Başarı mesajı göster
      const basarili_toplam = (data.basarili_user || 0) + (data.basarili_bayi || 0)
      if (basarili_toplam > 0) {
        const mesaj = []
        if (data.basarili_user > 0) mesaj.push(`${data.basarili_user} kullanıcı`)
        if (data.basarili_bayi > 0) mesaj.push(`${data.basarili_bayi} bayi`)
        toast.success(`${mesaj.join(' ve ')} başarıyla yüklendi!`)
        queryClient.invalidateQueries(['users'])
      }
      
      if (data.basarisiz > 0) {
        toast.warning(`${data.basarisiz} satır hatalı`)
      }
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Excel yüklenemedi')
      setUploadResult(null)
    }
  })

  // Template indirme
  const handleDownloadTemplate = async () => {
    try {
      const response = await axios.get('/api/auth/download-user-template', {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'Kullanici_Sablonu.xlsx')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
      toast.success('Template indirildi')
    } catch (error) {
      console.error('Template indirme hatası:', error)
      toast.error('Template indirilemedi')
    }
  }

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  // KVKK Modal işlemleri
  const handleViewKVKK = async (user) => {
    setSelectedUserForKVKK(user)
    setShowKVKKModal(true)
    setKvkkLoading(true)
    setKvkkConsent(null)
    
    try {
      const response = await axios.get(`/api/kvkk/admin/consent/${user.id}`)
      setKvkkConsent(response.data)
    } catch (error) {
      if (error.response?.status === 404) {
        toast.info('Bu kullanıcı henüz KVKK onayı vermemiş')
      } else if (error.response?.status === 403) {
        toast.error('Bu işlem için admin yetkisi gerekli')
        setShowKVKKModal(false)
      } else {
        toast.error('KVKK bilgileri alınamadı')
      }
    } finally {
      setKvkkLoading(false)
    }
  }

  const handleDeleteKVKKClick = () => {
    setShowDeleteKVKKConfirm(true)
  }

  const handleConfirmDeleteKVKK = async () => {
    if (!selectedUserForKVKK) return
    
    try {
      await axios.delete(`/api/kvkk/admin/consent/${selectedUserForKVKK.id}`)
      toast.success('KVKK onayları silindi. Kullanıcı tekrar onay vermek zorunda.')
      setShowDeleteKVKKConfirm(false)
      setShowKVKKModal(false)
      setKvkkConsent(null)
    } catch (error) {
      if (error.response?.status === 404) {
        toast.info('KVKK onayı zaten mevcut değil')
      } else if (error.response?.status === 403) {
        toast.error('Bu işlem için admin yetkisi gerekli')
      } else {
        toast.error('KVKK onayları silinemedi')
      }
      setShowDeleteKVKKConfirm(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Validasyon
    if (!formData.username || !formData.email || !formData.password || !formData.full_name) {
      toast.error('Lütfen zorunlu alanları doldurun')
      return
    }
    
    createMutation.mutate(formData)
  }

  const handleEdit = (user) => {
    setSelectedUser(user)
    setShowModal(true)
  }

  const handleUpdate = (e) => {
    e.preventDefault()
    
    if (!selectedUser) return
    
    const updateData = {
      email: selectedUser.email,
      full_name: selectedUser.full_name,
      company_name: selectedUser.company_name,
      tax_number: selectedUser.tax_number,
      phone: selectedUser.phone,
      address: selectedUser.address,
      role: selectedUser.role,
      is_active: selectedUser.is_active
    }
    
    // Şifre değiştirildiyse ekle
    if (selectedUser.new_password) {
      updateData.password = selectedUser.new_password
    }
    
    updateMutation.mutate({ id: selectedUser.id, data: updateData })
  }

  const handleToggleActive = (userId, username, isActive) => {
    const action = isActive ? 'pasif' : 'aktif'
    if (window.confirm(`${username} kullanıcısını ${action} yapmak istediğinizden emin misiniz?`)) {
      toggleActiveMutation.mutate(userId)
    }
  }

  const handleDelete = (userId, username) => {
    if (window.confirm(`UYARI: ${username} kullanıcısı kalıcı olarak silinecek!\n\nBu işlem geri alınamaz. Devam etmek istiyor musunuz?`)) {
      deleteMutation.mutate(userId)
    }
  }

  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      password: '',
      full_name: '',
      company_name: '',
      tax_number: '',
      phone: '',
      address: '',
      role: 'musteri',
      bayi_kodu: ''
    })
    setShowPassword(false)
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        toast.error('Lütfen Excel dosyası seçiniz (.xlsx veya .xls)')
        return
      }
      
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Dosya boyutu maksimum 5 MB olmalıdır')
        return
      }
      
      setExcelFile(file)
      setUploadResult(null)
    }
  }

  const handleExcelUpload = () => {
    if (!excelFile) {
      toast.error('Lütfen bir Excel dosyası seçiniz')
      return
    }
    
    uploadExcelMutation.mutate(excelFile)
  }

  const getRoleBadge = (role) => {
    const roleMap = {
      'admin': { label: 'Admin', color: 'red' },
      'muhasebe': { label: 'Muhasebe', color: 'blue' },
      'planlama': { label: 'Planlama', color: 'purple' },
      'musteri': { label: 'Müşteri', color: 'green' },
      'tedarikci': { label: 'Tedarikçi', color: 'orange' }
    }
    
    const roleInfo = roleMap[role] || { label: role, color: 'gray' }
    return <span className={`role-badge role-${roleInfo.color}`}>{roleInfo.label}</span>
  }

  // Advanced Filter Helpers
  const getActiveFilters = () => {
    const filters = []
    if (dateStart || dateEnd) {
      const dateText = dateStart && dateEnd 
        ? `${dateStart} - ${dateEnd}` 
        : dateStart || dateEnd
      filters.push({ key: 'date', label: 'Kayıt Tarihi', value: dateText })
    }
    if (selectedCompany) {
      filters.push({ key: 'company', label: 'Şirket', value: selectedCompany })
    }
    if (selectedRoles.length > 0) {
      const roleLabels = selectedRoles.map(r => {
        const roleMap = {
          'admin': 'Admin', 'muhasebe': 'Muhasebe', 'planlama': 'Planlama',
          'musteri': 'Müşteri', 'tedarikci': 'Tedarikçi'
        }
        return roleMap[r] || r
      }).join(', ')
      filters.push({ key: 'roles', label: 'Roller', value: roleLabels })
    }
    if (activeFilter !== '') {
      filters.push({ key: 'active', label: 'Durum', value: activeFilter === 'true' ? 'Aktif' : 'Pasif' })
    }
    if (roleFilter) {
      const roleMap = {
        'admin': 'Admin', 'muhasebe': 'Muhasebe', 'planlama': 'Planlama',
        'musteri': 'Müşteri', 'tedarikci': 'Tedarikçi'
      }
      filters.push({ key: 'role', label: 'Rol', value: roleMap[roleFilter] || roleFilter })
    }
    return filters
  }

  const clearAllFilters = () => {
    setDateStart('')
    setDateEnd('')
    setSelectedCompany('')
    setSelectedRoles([])
    setRoleFilter('')
    setActiveFilter('')
    setPage(1)
  }

  const removeFilter = (filterKey) => {
    switch(filterKey) {
      case 'date':
        setDateStart('')
        setDateEnd('')
        break
      case 'company':
        setSelectedCompany('')
        break
      case 'roles':
        setSelectedRoles([])
        break
      case 'active':
        setActiveFilter('')
        break
      case 'role':
        setRoleFilter('')
        break
    }
    setPage(1)
  }

  const activeFilters = getActiveFilters()
  const activeFilterCount = activeFilters.length

  return (
    <div className="user-management">
      <div className="user-header">
        <div>
          <h1>Kullanıcı Yönetimi</h1>
          <p>Sistem kullanıcılarını yönetin</p>
        </div>
        <div className="user-stats">
          <div className="stat-item">
            <FaUsers />
            <div>
              <span className="stat-number">{users?.length || 0}</span>
              <span className="stat-label">Toplam Kullanıcı</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Buttons */}
      <div className="tab-buttons">
        <button
          type="button"
          className={`tab-button ${activeTab === 'list' ? 'active' : ''}`}
          onClick={() => setActiveTab('list')}
        >
          <FaUsers /> Kullanıcı Listesi
        </button>
        <button
          type="button"
          className={`tab-button ${activeTab === 'add' ? 'active' : ''}`}
          onClick={() => setActiveTab('add')}
        >
          <FaUserPlus /> Yeni Kullanıcı
        </button>
        <button
          type="button"
          className={`tab-button ${activeTab === 'excel' ? 'active' : ''}`}
          onClick={() => setActiveTab('excel')}
        >
          <FaFileExcel /> Excel'den Yükle
        </button>
      </div>

      {/* Kullanıcı Listesi */}
      {activeTab === 'list' && (
        <div className="user-list-section">
          <div className="card">
            <h3><FaUsers /> Kayıtlı Kullanıcılar ({metadata.total_items || 0})</h3>
            
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
              <FilterGroup label="Kayıt Tarihi Aralığı" columns={1}>
                <DateRangePicker
                  startDate={dateStart}
                  endDate={dateEnd}
                  onStartDateChange={setDateStart}
                  onEndDateChange={setDateEnd}
                  presets={true}
                />
              </FilterGroup>

              <FilterGroup label="Filtreler" columns={2}>
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
                    value={activeFilter}
                    onChange={(e) => {
                      setActiveFilter(e.target.value)
                      setPage(1)
                    }}
                  >
                    <option value="">Tüm Durumlar</option>
                    <option value="true">Aktif</option>
                    <option value="false">Pasif</option>
                  </select>
                </FilterItem>
              </FilterGroup>

              <FilterGroup label="Rol Seçimi (Multi-Select)" columns={1}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {['admin', 'company_admin', 'muhasebe', 'planlama', 'musteri', 'tedarikci'].map(role => {
                    const roleLabels = {
                      'admin': 'Admin',
                      'company_admin': 'Şirket Admini',
                      'muhasebe': 'Muhasebe',
                      'planlama': 'Planlama',
                      'musteri': 'Müşteri',
                      'tedarikci': 'Tedarikçi'
                    }
                    const isSelected = selectedRoles.includes(role)
                    return (
                      <button
                        key={role}
                        type="button"
                        onClick={() => {
                          if (isSelected) {
                            setSelectedRoles(selectedRoles.filter(r => r !== role))
                          } else {
                            setSelectedRoles([...selectedRoles, role])
                          }
                          setPage(1)
                        }}
                        style={{
                          padding: '8px 16px',
                          border: `2px solid ${isSelected ? '#3b82f6' : '#e5e7eb'}`,
                          backgroundColor: isSelected ? '#3b82f6' : 'white',
                          color: isSelected ? 'white' : '#374151',
                          borderRadius: '20px',
                          cursor: 'pointer',
                          fontSize: '13px',
                          fontWeight: '500',
                          transition: 'all 0.2s ease'
                        }}
                      >
                        {isSelected && '✓ '}{roleLabels[role]}
                      </button>
                    )
                  })}
                </div>
              </FilterGroup>
            </FilterPanel>
            
            {/* Filtreleme ve Arama */}
            <div className="filters-container" style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
              <input
                type="text"
                placeholder="Ara (kullanıcı adı, ad soyad, email, VKN/TC)..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value)
                  setPage(1)
                }}
                style={{ flex: '1', minWidth: '250px', padding: '0.6rem', borderRadius: '8px', border: '1px solid #ddd' }}
              />
              <select 
                value={roleFilter} 
                onChange={(e) => {
                  setRoleFilter(e.target.value)
                  setPage(1)
                }}
                style={{ padding: '0.6rem', borderRadius: '8px', border: '1px solid #ddd' }}
              >
                <option value="">Tüm Roller</option>
                <option value="admin">Admin</option>
                <option value="company_admin">Şirket Admini</option>
                <option value="muhasebe">Muhasebe</option>
                <option value="planlama">Planlama</option>
                <option value="musteri">Müşteri</option>
                <option value="tedarikci">Tedarikçi</option>
              </select>
              <select 
                value={activeFilter} 
                onChange={(e) => {
                  setActiveFilter(e.target.value)
                  setPage(1)
                }}
                style={{ padding: '0.6rem', borderRadius: '8px', border: '1px solid #ddd' }}
              >
                <option value="">Tüm Durumlar</option>
                <option value="true">Aktif</option>
                <option value="false">Pasif</option>
              </select>
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

            {/* Pagination Info */}
            {metadata.total_items > 0 && (
              <div style={{ marginBottom: '1rem', color: '#666', fontSize: '0.9rem' }}>
                Toplam {metadata.total_items} kullanıcı bulundu (Sayfa {page} / {metadata.total_pages})
              </div>
            )}
            
            {/* Loading State */}
            {isLoading ? (
              <div className="user-table-wrapper animate-fadeIn">
                <SkeletonLoader type="table-row" count={10} />
              </div>
            ) : users && users.length > 0 ? (
              <div className="user-table-wrapper animate-fadeInUp">
                <table className="user-table">
                  <thead>
                    <tr>
                      <th>Kullanıcı Adı</th>
                      <th>Ad Soyad</th>
                      <th>E-posta</th>
                      <th>Firma</th>
                      <th>Rol</th>
                      <th>Durum</th>
                      <th>İşlemler</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td><strong>{user.username}</strong></td>
                        <td>{user.full_name}</td>
                        <td>{user.email}</td>
                        <td>{user.company_name || '-'}</td>
                        <td>{getRoleBadge(user.role)}</td>
                        <td>
                          {user.is_active ? (
                            <span className="status-badge status-active">Aktif</span>
                          ) : (
                            <span className="status-badge status-inactive">Pasif</span>
                          )}
                        </td>
                        <td>
                          <div className="action-buttons">
                            <button
                              className="btn-icon btn-edit"
                              onClick={() => handleEdit(user)}
                              title="Düzenle"
                            >
                              <FaEdit />
                            </button>
                            <button
                              className="btn-icon btn-info"
                              onClick={() => handleViewKVKK(user)}
                              title="KVKK Onaylarını Görüntüle"
                            >
                              <FaShieldAlt />
                            </button>
                            <button
                              className={`btn-icon ${user.is_active ? 'btn-warning' : 'btn-success'}`}
                              onClick={() => handleToggleActive(user.id, user.username, user.is_active)}
                              title={user.is_active ? 'Pasif Yap' : 'Aktif Yap'}
                            >
                              {user.is_active ? <FaBan /> : <FaToggleOn />}
                            </button>
                            <button
                              className="btn-icon btn-delete"
                              onClick={() => handleDelete(user.id, user.username)}
                              title="Kalıcı Olarak Sil"
                            >
                              <FaTrash />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                {/* Pagination Controls */}
                {metadata.total_pages > 1 && (
                  <div className="pagination-controls">
                    <button
                      className="pagination-btn"
                      onClick={() => setPage(1)}
                      disabled={page === 1}
                    >
                      İlk
                    </button>
                    <button
                      className="pagination-btn"
                      onClick={() => setPage(p => p - 1)}
                      disabled={!metadata.has_prev}
                    >
                      Önceki
                    </button>
                    
                    <div className="pagination-numbers">
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
                            className={`pagination-number ${page === pageNum ? 'active' : ''}`}
                            onClick={() => setPage(pageNum)}
                          >
                            {pageNum}
                          </button>
                        )
                      })}
                    </div>
                    
                    <button
                      className="pagination-btn"
                      onClick={() => setPage(p => p + 1)}
                      disabled={!metadata.has_next}
                    >
                      Sonraki
                    </button>
                    <button
                      className="pagination-btn"
                      onClick={() => setPage(metadata.total_pages)}
                      disabled={page === metadata.total_pages}
                    >
                      Son
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <FaUsers />
                <p>{searchTerm || roleFilter || activeFilter ? 'Aramanıza uygun kullanıcı bulunamadı' : 'Henüz kullanıcı bulunmuyor'}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Yeni Kullanıcı Formu */}
      {activeTab === 'add' && (
        <div className="user-add-section">
          <div className="card">
            <h3><FaUserPlus /> Yeni Kullanıcı Ekle</h3>
            
            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                <div className="form-group">
                  <label>Kullanıcı Adı *</label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                    placeholder="ornek_kullanici"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>E-posta *</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="ornek@firma.com"
                    required
                  />
                </div>

                <div className="form-group password-group">
                  <label>Şifre *</label>
                  <div className="password-input">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      placeholder="En az 6 karakter"
                      required
                      minLength={6}
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <FaEyeSlash /> : <FaEye />}
                    </button>
                  </div>
                </div>

                <div className="form-group">
                  <label>Ad Soyad *</label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    placeholder="Ali Yılmaz"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Firma Adı</label>
                  <input
                    type="text"
                    name="company_name"
                    value={formData.company_name}
                    onChange={handleInputChange}
                    placeholder="ABC Ltd. Şti."
                  />
                </div>

                <div className="form-group">
                  <label>Vergi Numarası</label>
                  <input
                    type="text"
                    name="tax_number"
                    value={formData.tax_number}
                    onChange={handleInputChange}
                    placeholder="1234567890"
                    maxLength={10}
                  />
                </div>

                <div className="form-group">
                  <label>Telefon</label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    placeholder="05321234567"
                  />
                </div>

                <div className="form-group">
                  <label>Rol *</label>
                  <select
                    name="role"
                    value={formData.role}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="musteri">Müşteri</option>
                    <option value="tedarikci">Tedarikçi</option>
                    <option value="muhasebe">Muhasebe</option>
                    <option value="planlama">Planlama</option>
                  </select>
                </div>

                {formData.role === 'musteri' && (
                  <div className="form-group">
                    <label>Bayi Kodu *</label>
                    <input
                      type="text"
                      name="bayi_kodu"
                      value={formData.bayi_kodu}
                      onChange={handleInputChange}
                      placeholder="BY001"
                      required
                    />
                    <small style={{ color: '#6c757d', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                      Müşteri için otomatik bayi kaydı oluşturulacaktır
                    </small>
                  </div>
                )}
              </div>

              <div className="form-group">
                <label>Adres</label>
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                  placeholder="Tam adres"
                  rows={3}
                />
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    resetForm()
                    setActiveTab('list')
                  }}
                >
                  İptal
                </button>
                <LoadingButton
                  type="submit"
                  loading={createMutation.isPending}
                  variant="primary"
                  icon={<FaUserPlus />}
                  loadingText="Oluşturuluyor..."
                >
                  Kullanıcı Oluştur
                </LoadingButton>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Excel Yükleme */}
      {activeTab === 'excel' && (
        <div className="excel-upload-section">
          <div className="card">
            <h3><FaFileExcel /> Excel Dosyasından Toplu Kullanıcı Yükleme</h3>
            <p className="info-text">
              Excel şablonunu indirip doldurun, ardından sisteme yükleyin. Kullanıcılar otomatik olarak oluşturulacaktır.
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
              >
                Yükle ve İşle
              </LoadingButton>
            </div>

            {/* Yükleme Sonuçları */}
            {uploadResult && (
              <div className="upload-result">
                <h3>Yükleme Sonuçları</h3>
                
                <div className="result-summary">
                  <div className="result-item total">
                    <FaUsers />
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

                {/* Başarılı Kullanıcılar */}
                {uploadResult.olusturulan_kullanicilar?.length > 0 && (
                  <div className="success-list">
                    <h4><FaCheckCircle /> Oluşturulan Kullanıcılar</h4>
                    <div className="success-items">
                      {uploadResult.olusturulan_kullanicilar.map((item, index) => (
                        <div key={index} className="success-item">
                          <span className="user-username">{item.username}</span>
                          <span className="user-name">{item.full_name}</span>
                          <span className="user-email">{item.email}</span>
                          {getRoleBadge(item.role)}
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
                          <span className="error-user">{error.kullanici}</span>
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
                    onClick={() => setActiveTab('list')}
                  >
                    Kullanıcı Listesine Git
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Düzenleme Modal */}
      {showModal && selectedUser && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3><FaEdit /> Kullanıcı Düzenle</h3>
              <button
                className="modal-close"
                onClick={() => setShowModal(false)}
              >
                <FaTimes />
              </button>
            </div>

            <form onSubmit={handleUpdate}>
              <div className="modal-body">
                <div className="form-grid">
                  <div className="form-group">
                    <label>Kullanıcı Adı</label>
                    <input
                      type="text"
                      value={selectedUser.username}
                      disabled
                      className="input-disabled"
                    />
                    <small>Kullanıcı adı değiştirilemez</small>
                  </div>

                  <div className="form-group">
                    <label>E-posta *</label>
                    <input
                      type="email"
                      value={selectedUser.email}
                      onChange={(e) => setSelectedUser({...selectedUser, email: e.target.value})}
                      required
                    />
                  </div>

                  <div className="form-group password-group">
                    <label>Yeni Şifre (Opsiyonel)</label>
                    <div className="password-input">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={selectedUser.new_password || ''}
                        onChange={(e) => setSelectedUser({...selectedUser, new_password: e.target.value})}
                        placeholder="Boş bırakın değiştirmek istemiyorsanız"
                        minLength={6}
                      />
                      <button
                        type="button"
                        className="password-toggle"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <FaEyeSlash /> : <FaEye />}
                      </button>
                    </div>
                  </div>

                  <div className="form-group">
                    <label>Ad Soyad *</label>
                    <input
                      type="text"
                      value={selectedUser.full_name}
                      onChange={(e) => setSelectedUser({...selectedUser, full_name: e.target.value})}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Firma Adı</label>
                    <input
                      type="text"
                      value={selectedUser.company_name || ''}
                      onChange={(e) => setSelectedUser({...selectedUser, company_name: e.target.value})}
                    />
                  </div>

                  <div className="form-group">
                    <label>Vergi Numarası</label>
                    <input
                      type="text"
                      value={selectedUser.tax_number || ''}
                      onChange={(e) => setSelectedUser({...selectedUser, tax_number: e.target.value})}
                      maxLength={10}
                    />
                  </div>

                  <div className="form-group">
                    <label>Telefon</label>
                    <input
                      type="tel"
                      value={selectedUser.phone || ''}
                      onChange={(e) => setSelectedUser({...selectedUser, phone: e.target.value})}
                    />
                  </div>

                  <div className="form-group">
                    <label>Rol *</label>
                    <select
                      value={selectedUser.role}
                      onChange={(e) => setSelectedUser({...selectedUser, role: e.target.value})}
                      required
                    >
                      <option value="musteri">Müşteri</option>
                      <option value="tedarikci">Tedarikçi</option>
                      <option value="muhasebe">Muhasebe</option>
                      <option value="planlama">Planlama</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label>Adres</label>
                  <textarea
                    value={selectedUser.address || ''}
                    onChange={(e) => setSelectedUser({...selectedUser, address: e.target.value})}
                    rows={3}
                  />
                </div>

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={selectedUser.is_active}
                      onChange={(e) => setSelectedUser({...selectedUser, is_active: e.target.checked})}
                    />
                    Aktif Kullanıcı
                  </label>
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  İptal
                </button>
                <LoadingButton
                  type="submit"
                  loading={updateMutation.isPending}
                  variant="primary"
                  icon={<FaSave />}
                  loadingText="Kaydediliyor..."
                >
                  Kaydet
                </LoadingButton>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* KVKK Modal */}
      {showKVKKModal && selectedUserForKVKK && (
        <div className="modal-overlay" onClick={() => setShowKVKKModal(false)}>
          <div className="modal-content kvkk-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3><FaShieldAlt /> KVKK Onayları - {selectedUserForKVKK.username}</h3>
              <button
                className="modal-close"
                onClick={() => setShowKVKKModal(false)}
              >
                <FaTimes />
              </button>
            </div>

            <div className="modal-body">
              {kvkkLoading ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <div className="spinner"></div>
                  <p>KVKK bilgileri yükleniyor...</p>
                </div>
              ) : kvkkConsent ? (
                <div className="kvkk-info">
                  <div className="kvkk-user-info">
                    <p><strong>Kullanıcı:</strong> {selectedUserForKVKK.full_name || selectedUserForKVKK.username}</p>
                    <p><strong>Email:</strong> {selectedUserForKVKK.email}</p>
                    <p><strong>Rol:</strong> {selectedUserForKVKK.role}</p>
                  </div>

                  <div className="kvkk-consents-grid">
                    <div className={`kvkk-consent-item ${kvkkConsent.kvkk_policy_accepted ? 'accepted' : 'rejected'}`}>
                      <div className="consent-header">
                        {kvkkConsent.kvkk_policy_accepted ? (
                          <FaCheckCircle className="icon-accepted" />
                        ) : (
                          <FaTimesCircle className="icon-rejected" />
                        )}
                        <h4>KVKK Politikası</h4>
                      </div>
                      {kvkkConsent.kvkk_policy_accepted && kvkkConsent.kvkk_policy_date && (
                        <div className="consent-details">
                          <p><strong>Onay Tarihi:</strong> {new Date(kvkkConsent.kvkk_policy_date).toLocaleString('tr-TR')}</p>
                          <p><strong>Versiyon:</strong> {kvkkConsent.kvkk_policy_version}</p>
                        </div>
                      )}
                    </div>

                    <div className={`kvkk-consent-item ${kvkkConsent.customer_notice_accepted ? 'accepted' : 'rejected'}`}>
                      <div className="consent-header">
                        {kvkkConsent.customer_notice_accepted ? (
                          <FaCheckCircle className="icon-accepted" />
                        ) : (
                          <FaTimesCircle className="icon-rejected" />
                        )}
                        <h4>Müşteri Aydınlatma Metni</h4>
                      </div>
                      {kvkkConsent.customer_notice_accepted && kvkkConsent.customer_notice_date && (
                        <div className="consent-details">
                          <p><strong>Onay Tarihi:</strong> {new Date(kvkkConsent.customer_notice_date).toLocaleString('tr-TR')}</p>
                          <p><strong>Versiyon:</strong> {kvkkConsent.customer_notice_version}</p>
                        </div>
                      )}
                    </div>

                    <div className={`kvkk-consent-item ${kvkkConsent.data_retention_accepted ? 'accepted' : 'rejected'}`}>
                      <div className="consent-header">
                        {kvkkConsent.data_retention_accepted ? (
                          <FaCheckCircle className="icon-accepted" />
                        ) : (
                          <FaTimesCircle className="icon-rejected" />
                        )}
                        <h4>Veri Saklama ve İmha Politikası</h4>
                      </div>
                      {kvkkConsent.data_retention_accepted && kvkkConsent.data_retention_date && (
                        <div className="consent-details">
                          <p><strong>Onay Tarihi:</strong> {new Date(kvkkConsent.data_retention_date).toLocaleString('tr-TR')}</p>
                          <p><strong>Versiyon:</strong> {kvkkConsent.data_retention_version}</p>
                        </div>
                      )}
                    </div>

                    <div className={`kvkk-consent-item ${kvkkConsent.system_consent_accepted ? 'accepted' : 'rejected'}`}>
                      <div className="consent-header">
                        {kvkkConsent.system_consent_accepted ? (
                          <FaCheckCircle className="icon-accepted" />
                        ) : (
                          <FaTimesCircle className="icon-rejected" />
                        )}
                        <h4>Sistem Onayı</h4>
                      </div>
                      {kvkkConsent.system_consent_accepted && kvkkConsent.system_consent_date && (
                        <div className="consent-details">
                          <p><strong>Onay Tarihi:</strong> {new Date(kvkkConsent.system_consent_date).toLocaleString('tr-TR')}</p>
                          <p><strong>Versiyon:</strong> {kvkkConsent.system_consent_version}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="kvkk-legal-info">
                    <h4>📌 Yasal Delil Bilgileri</h4>
                    <div className="legal-info-grid">
                      <div className="legal-info-item">
                        <strong>IP Adresi:</strong>
                        <span>{kvkkConsent.ip_address || 'N/A'}</span>
                      </div>
                      <div className="legal-info-item">
                        <strong>ISP:</strong>
                        <span>{kvkkConsent.isp || 'N/A'}</span>
                      </div>
                      <div className="legal-info-item">
                        <strong>Şehir:</strong>
                        <span>{kvkkConsent.city || 'N/A'}</span>
                      </div>
                      <div className="legal-info-item">
                        <strong>Ülke:</strong>
                        <span>{kvkkConsent.country || 'N/A'}</span>
                      </div>
                      <div className="legal-info-item">
                        <strong>Organizasyon:</strong>
                        <span>{kvkkConsent.organization || 'N/A'}</span>
                      </div>
                      <div className="legal-info-item">
                        <strong>Kayıt Tarihi:</strong>
                        <span>{new Date(kvkkConsent.created_at).toLocaleString('tr-TR')}</span>
                      </div>
                    </div>
                    {kvkkConsent.user_agent && (
                      <div className="legal-info-item" style={{ marginTop: '10px' }}>
                        <strong>User Agent:</strong>
                        <span style={{ fontSize: '11px', wordBreak: 'break-all' }}>{kvkkConsent.user_agent}</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <FaShieldAlt size={48} style={{ color: '#ccc', marginBottom: '20px' }} />
                  <p style={{ fontSize: '16px', color: '#666' }}>
                    Bu kullanıcı henüz KVKK onayı vermemiş.
                  </p>
                  <p style={{ fontSize: '14px', color: '#999' }}>
                    Kullanıcı ilk girişinde KVKK onaylarını vermelidir.
                  </p>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => setShowKVKKModal(false)}
              >
                Kapat
              </button>
              {kvkkConsent && (
                <button
                  className="btn btn-delete"
                  onClick={handleDeleteKVKKClick}
                >
                  <FaTrash /> KVKK Onaylarını Sil
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* KVKK Silme Onay Popup */}
      {showDeleteKVKKConfirm && selectedUserForKVKK && (
        <div className="modal-overlay" style={{ zIndex: 10001 }} onClick={() => setShowDeleteKVKKConfirm(false)}>
          <div className="confirmation-popup" onClick={(e) => e.stopPropagation()}>
            <div className="confirmation-header">
              <h3>localhost:3000 web sitesinin mesajı</h3>
            </div>
            <div className="confirmation-body">
              <p><strong>{selectedUserForKVKK.username}</strong> kullanıcısının KVKK onaylarını silmek istediğinize emin misiniz?</p>
              <p className="confirmation-warning">Kullanıcı bir sonraki girişinde tekrar onay vermek zorunda kalacak.</p>
            </div>
            <div className="confirmation-footer">
              <button
                className="btn-confirm-ok"
                onClick={handleConfirmDeleteKVKK}
              >
                Tamam
              </button>
              <button
                className="btn-confirm-cancel"
                onClick={() => setShowDeleteKVKKConfirm(false)}
              >
                İptal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

