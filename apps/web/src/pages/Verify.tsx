import { useParams } from 'react-router-dom'

export default function Verify() {
  const { badgeId } = useParams()

  return (
    <div style={{ minHeight: '100vh', background: '#0B0D1A', color: '#F1F5F9', fontFamily: 'Inter, system-ui, sans-serif', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', maxWidth: 500, padding: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>Badge Verification</h1>
        <p style={{ color: '#94A3B8' }}>Badge ID: {badgeId}</p>
        <p style={{ color: '#475569', marginTop: '1rem' }}>Verification not yet implemented.</p>
      </div>
    </div>
  )
}
