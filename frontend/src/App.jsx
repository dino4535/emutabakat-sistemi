import { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import MutabakatList from './pages/MutabakatList'
import MutabakatCreate from './pages/MutabakatCreate'
import MutabakatCreateVKN from './pages/MutabakatCreateVKN'
import MutabakatDetail from './pages/MutabakatDetail'
import BulkMutabakat from './pages/BulkMutabakat'
import BayiBulkUpload from './pages/BayiBulkUpload'
import Profile from './pages/Profile'
import PublicApproval from './pages/PublicApproval'
import ApprovalSuccess from './pages/ApprovalSuccess'
import Reports from './pages/Reports'
import LegalReports from './pages/LegalReports'
import VerifySignature from './pages/VerifySignature'
import UserManagement from './pages/UserManagement'
import CompanyManagement from './pages/CompanyManagement'
import KVKKPopup from './components/KVKKPopup'
import axios from 'axios'
import { toast } from 'react-toastify'

function PrivateRoute({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" />
}

function App() {
  const { user } = useAuth()
  const [showKVKKPopup, setShowKVKKPopup] = useState(false)
  const [kvkkChecked, setKvkkChecked] = useState(false)

  // Kullanıcı login olduğunda KVKK kontrolü yap
  useEffect(() => {
    const checkKVKK = async () => {
      if (user && !kvkkChecked) {
        console.log('[APP] User login oldu, KVKK kontrol ediliyor...')
        try {
          const response = await axios.get('/api/kvkk/consent/check')
          console.log('[APP] KVKK Response:', response.data)
          
          if (!response.data.all_consents_given) {
            console.log('[APP] KVKK onaylari eksik, popup aciliyor!')
            setShowKVKKPopup(true)
            toast.warning('⚠️ KVKK onaylarınız tamamlanmalı')
          } else {
            console.log('[APP] KVKK onaylari tamam')
          }
          setKvkkChecked(true)
        } catch (error) {
          console.error('[APP] KVKK kontrol hatasi:', error)
          if (error.response?.status === 404) {
            console.log('[APP] KVKK kaydi yok, popup aciliyor!')
            setShowKVKKPopup(true)
            toast.warning('⚠️ KVKK onaylarınızı vermeniz gerekmektedir')
          }
          setKvkkChecked(true)
        }
      } else if (!user) {
        // Kullanıcı logout olduğunda reset et
        setKvkkChecked(false)
      }
    }

    checkKVKK()
  }, [user, kvkkChecked])

  const handleKVKKComplete = () => {
    console.log('[APP] KVKK onaylari tamamlandi, popup kapatiliyor')
    setShowKVKKPopup(false)
    toast.success('KVKK onayları kaydedildi')
    
    // İlk girişse profil sayfasına yönlendir
    if (user?.ilk_giris_tamamlandi === false) {
      console.log('[APP] İlk giriş, profil sayfasına yönlendiriliyor...')
      toast.info('Lütfen profil bilgilerinizi tamamlayın')
      setTimeout(() => {
        window.location.href = '/profile'
      }, 1500)
    }
  }

  return (
    <>
      {/* Global KVKK Popup */}
      {showKVKKPopup && user && <KVKKPopup onComplete={handleKVKKComplete} />}
      
      <Routes>
        {/* Public Routes - Authentication gerektirmez */}
        <Route path="/mutabakat/onay/:token" element={<PublicApproval />} />
        <Route path="/mutabakat/onay/basarili" element={<ApprovalSuccess />} />
        
        {/* Auth Routes */}
        <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <Login />} />
        <Route path="/register" element={user ? <Navigate to="/dashboard" /> : <Register />} />
        
        {/* Private Routes - Authentication gerektirir */}
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="mutabakat" element={<MutabakatList />} />
          <Route path="mutabakat/new" element={<MutabakatCreateVKN />} />
          <Route path="mutabakat/bulk" element={<BulkMutabakat />} />
          <Route path="mutabakat/:id" element={<MutabakatDetail />} />
          <Route path="bayi/bulk" element={<BayiBulkUpload />} />
          <Route path="reports" element={<Reports />} />
          <Route path="legal-reports" element={<LegalReports />} />
          <Route path="verify" element={<VerifySignature />} />
          <Route path="verify/mutabakat/:mutabakatNo" element={<VerifySignature />} />
          <Route path="users" element={<UserManagement />} />
          <Route path="companies" element={<CompanyManagement />} />
          <Route path="profile" element={<Profile />} />
        </Route>
      </Routes>
    </>
  )
}

export default App

