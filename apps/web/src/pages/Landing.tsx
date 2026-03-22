export default function Landing() {
  return (
    <div style={{ minHeight: '100vh', background: '#0B0D1A', color: '#F1F5F9', fontFamily: 'Inter, system-ui, sans-serif', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', maxWidth: 600, padding: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '1rem' }}>
          <span style={{ background: 'linear-gradient(135deg, #A78BFA, #60A5FA, #EC41FB)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            PromptRanks
          </span>
        </h1>
        <p style={{ fontSize: '1.2rem', color: '#94A3B8', marginBottom: '2rem', lineHeight: 1.7 }}>
          Measure your AI prompting skill. Get a verifiable badge. Share it with the world.
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            style={{ padding: '14px 32px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg, #6D5FFA, #8B5CF6, #EC41FB)', color: '#fff', fontSize: '1rem', fontWeight: 600, cursor: 'pointer' }}
          >
            Quick Assessment (15 min)
          </button>
          <button
            style={{ padding: '14px 32px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.15)', background: 'transparent', color: '#94A3B8', fontSize: '1rem', fontWeight: 600, cursor: 'pointer' }}
          >
            Full Assessment (~60 min)
          </button>
        </div>
        <p style={{ marginTop: '2rem', fontSize: '0.85rem', color: '#475569' }}>
          Powered by the PECAM Framework — Open Source
        </p>
      </div>
    </div>
  )
}
