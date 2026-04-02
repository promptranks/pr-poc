import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Landing from './pages/Landing'
import Assessment from './pages/Assessment'
import AssessmentDetail from './pages/AssessmentDetail'
import Badge from './pages/Badge'
import Verify from './pages/Verify'
import Leaderboard from './pages/Leaderboard'
import AuthCallback from './pages/AuthCallback'
import Dashboard from './pages/Dashboard'
import ProtectedRoute from './components/ProtectedRoute'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/assessment/:id" element={<Assessment />} />
          <Route path="/dashboard/assessment/:id" element={<ProtectedRoute><AssessmentDetail /></ProtectedRoute>} />
          <Route path="/badge/:badgeId" element={<Badge />} />
          <Route path="/verify/:badgeId" element={<Verify />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
