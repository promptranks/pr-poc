import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import Verify from './pages/Verify'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/verify/:badgeId" element={<Verify />} />
        {/* TODO: Step 3+ */}
        {/* <Route path="/assessment" element={<Assessment />} /> */}
        {/* <Route path="/results/:id" element={<Results />} /> */}
      </Routes>
    </BrowserRouter>
  )
}
