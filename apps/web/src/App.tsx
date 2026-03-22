import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import Assessment from './pages/Assessment'
import Verify from './pages/Verify'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/assessment/:id" element={<Assessment />} />
        <Route path="/verify/:badgeId" element={<Verify />} />
      </Routes>
    </BrowserRouter>
  )
}
