import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import Assessment from './pages/Assessment'
import Badge from './pages/Badge'
import Verify from './pages/Verify'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/assessment/:id" element={<Assessment />} />
        <Route path="/badge/:badgeId" element={<Badge />} />
        <Route path="/verify/:badgeId" element={<Verify />} />
      </Routes>
    </BrowserRouter>
  )
}
