import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const INDUSTRIES = [
  'Technology', 'Finance', 'Healthcare', 'Education', 'Marketing',
  'Legal', 'Manufacturing', 'Consulting', 'Government', 'Other',
]

const ROLES = [
  'Software Engineer', 'Product Manager', 'Data Scientist', 'Designer',
  'Marketing Manager', 'Business Analyst', 'Executive', 'Student',
  'Researcher', 'Freelancer', 'Other',
]

const LEVEL_COLORS: Record<number, string> = {
  1: '#666666',
  2: '#008f11',
  3: '#00ff41',
  4: '#6D5FFA',
  5: '#EC41FB',
}

interface TopEntry {
  rank: number
  user_id: string
  display_name: string
  level: number
  level_name: string
  score: number
}

const PILLARS = [
  { letter: 'P', name: 'Prompt Design', desc: 'Crafting effective prompts' },
  { letter: 'E', name: 'Evaluation', desc: 'Judging output quality' },
  { letter: 'C', name: 'Context Management', desc: 'Managing context windows' },
  { letter: 'M', name: 'Meta-Cognition', desc: 'Understanding AI limits' },
  { letter: 'A', name: 'Agentic Prompting', desc: 'Multi-step workflows' },
]

const styles = {
  page: {
    minHeight: '100vh',
    background: '#000000',
    color: '#c0ffc0',
    fontFamily: "'Share Tech Mono', monospace",
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
  },
  container: {
    maxWidth: 800,
    width: '100%',
    padding: '3rem 2rem',
    textAlign: 'center' as const,
  },
  heading: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '1.6rem',
    color: '#00ff41',
    marginBottom: '0.5rem',
    textShadow: '0 0 20px rgba(0,255,65,0.4)',
  },
  subheading: {
    fontSize: '1.1rem',
    color: '#008f11',
    marginBottom: '2.5rem',
    lineHeight: 1.6,
  },
  buttonRow: {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'center',
    flexWrap: 'wrap' as const,
    marginBottom: '2rem',
  },
  ctaButton: {
    padding: '16px 36px',
    borderRadius: 4,
    border: 'none',
    background: 'linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 40%, #EC41FB 100%)',
    color: '#fff',
    fontSize: '1rem',
    fontFamily: "'Share Tech Mono', monospace",
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s',
    boxShadow: '0 0 20px rgba(109,95,250,0.3)',
  },
  secondaryButton: {
    padding: '16px 36px',
    borderRadius: 4,
    border: '1px solid rgba(0,255,65,0.2)',
    background: 'rgba(0,15,0,0.6)',
    color: '#00ff41',
    fontSize: '1rem',
    fontFamily: "'Share Tech Mono', monospace",
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  disabledButton: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  dropdownRow: {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'center',
    flexWrap: 'wrap' as const,
    marginBottom: '2.5rem',
  },
  select: {
    padding: '10px 16px',
    borderRadius: 4,
    border: '1px solid rgba(0,255,65,0.2)',
    background: 'rgba(0,15,0,0.6)',
    color: '#c0ffc0',
    fontSize: '0.9rem',
    fontFamily: "'Share Tech Mono', monospace",
    cursor: 'pointer',
    minWidth: 200,
    appearance: 'none' as const,
  },
  section: {
    marginTop: '3rem',
    padding: '2rem',
    border: '1px solid rgba(0,255,65,0.1)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.6)',
  },
  sectionTitle: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.75rem',
    color: '#00ff41',
    marginBottom: '1.5rem',
    textTransform: 'uppercase' as const,
    letterSpacing: '2px',
  },
  pillarGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
    gap: '1rem',
  },
  pillarCard: {
    padding: '1rem',
    border: '1px solid rgba(0,255,65,0.15)',
    borderRadius: 4,
    background: 'rgba(0,15,0,0.4)',
    textAlign: 'center' as const,
  },
  pillarLetter: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '1.2rem',
    color: '#00ff41',
    textShadow: '0 0 10px rgba(0,255,65,0.4)',
    marginBottom: '0.5rem',
  },
  pillarName: {
    fontSize: '0.85rem',
    color: '#c0ffc0',
    marginBottom: '0.3rem',
  },
  pillarDesc: {
    fontSize: '0.75rem',
    color: '#008f11',
  },
  stepsRow: {
    display: 'flex',
    justifyContent: 'center',
    gap: '2rem',
    flexWrap: 'wrap' as const,
    marginTop: '1rem',
  },
  step: {
    textAlign: 'center' as const,
    maxWidth: 160,
  },
  stepNumber: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '1.5rem',
    color: '#6D5FFA',
    marginBottom: '0.5rem',
  },
  stepLabel: {
    fontSize: '0.9rem',
    color: '#c0ffc0',
  },
  footer: {
    marginTop: '3rem',
    paddingTop: '1.5rem',
    borderTop: '1px solid rgba(0,255,65,0.1)',
    fontSize: '0.8rem',
    color: '#008f11',
  },
  error: {
    color: '#ff4444',
    fontSize: '0.9rem',
    marginBottom: '1rem',
  },
}

export default function Landing() {
  const navigate = useNavigate()
  const [industry, setIndustry] = useState('')
  const [role, setRole] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [topEntries, setTopEntries] = useState<TopEntry[]>([])

  useEffect(() => {
    fetch(`${API_BASE}/leaderboard/?period=alltime&page=1&page_size=5`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => { if (d?.entries) setTopEntries(d.entries) })
      .catch(() => {})
  }, [])

  const startAssessment = async (mode: 'quick' | 'full') => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/assessments/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode,
          industry: industry || null,
          role: role || null,
        }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to start assessment')
      }

      const data = await res.json()
      // Store assessment data in sessionStorage for the assessment page
      sessionStorage.setItem('assessment', JSON.stringify(data))
      navigate(`/assessment/${data.assessment_id}`)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to start assessment'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <h1 style={styles.heading}>PromptRanks</h1>
        <p style={styles.subheading}>
          Measure your AI prompting skill in 15 minutes.<br />
          Get scored. Get a badge. Share it with the world.
        </p>

        {error && <p style={styles.error}>{error}</p>}

        <div style={styles.dropdownRow}>
          <select
            style={styles.select}
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
          >
            <option value="">Industry (optional)</option>
            {INDUSTRIES.map((i) => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
          <select
            style={styles.select}
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option value="">Role (optional)</option>
            {ROLES.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>

        <div style={styles.buttonRow}>
          <button
            style={{
              ...styles.ctaButton,
              ...(loading ? styles.disabledButton : {}),
            }}
            onClick={() => startAssessment('quick')}
            disabled={loading}
          >
            {loading ? '[ INITIALIZING... ]' : 'Quick Assessment (15 min)'}
          </button>
          <button
            style={{
              ...styles.secondaryButton,
              ...(loading ? styles.disabledButton : {}),
            }}
            onClick={() => startAssessment('full')}
            disabled={loading}
          >
            {loading ? '[ INITIALIZING... ]' : 'Full Assessment (~60 min)'}
          </button>
        </div>

        {/* PECAM Framework */}
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>The PECAM Framework</h2>
          <div style={styles.pillarGrid}>
            {PILLARS.map((p) => (
              <div key={p.letter} style={styles.pillarCard}>
                <div style={styles.pillarLetter}>{p.letter}</div>
                <div style={styles.pillarName}>{p.name}</div>
                <div style={styles.pillarDesc}>{p.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* How it works */}
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>How It Works</h2>
          <div style={styles.stepsRow}>
            <div style={styles.step}>
              <div style={styles.stepNumber}>01</div>
              <div style={styles.stepLabel}>Assess</div>
              <div style={{ ...styles.pillarDesc, marginTop: '0.3rem' }}>
                Answer KBA questions + write prompts
              </div>
            </div>
            <div style={styles.step}>
              <div style={styles.stepNumber}>02</div>
              <div style={styles.stepLabel}>Score</div>
              <div style={{ ...styles.pillarDesc, marginTop: '0.3rem' }}>
                AI judges your prompting skill
              </div>
            </div>
            <div style={styles.step}>
              <div style={styles.stepNumber}>03</div>
              <div style={styles.stepLabel}>Share</div>
              <div style={{ ...styles.pillarDesc, marginTop: '0.3rem' }}>
                Earn a verifiable badge
              </div>
            </div>
          </div>
        </div>

        {/* Leaderboard Preview */}
        <div id="leaderboard" style={styles.section}>
          <h2 style={styles.sectionTitle}>Top Prompt Engineers</h2>
          {topEntries.length === 0 ? (
            <p style={styles.pillarDesc}>No entries yet. Complete a Full Assessment to rank up.</p>
          ) : (
            <div style={{ marginBottom: '1rem' }}>
              {topEntries.map((entry) => (
                <div
                  key={entry.user_id ?? entry.rank}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    padding: '0.6rem 0',
                    borderBottom: '1px solid rgba(0,255,65,0.08)',
                  }}
                >
                  <span
                    style={{
                      fontFamily: "'Press Start 2P', monospace",
                      fontSize: '0.65rem',
                      color: entry.rank <= 3 ? ['', '#FFD700', '#C0C0C0', '#CD7F32'][entry.rank] : '#008f11',
                      minWidth: 24,
                    }}
                  >
                    #{entry.rank}
                  </span>
                  <span style={{ flex: 1, fontSize: '0.9rem', color: '#c0ffc0' }}>
                    {entry.display_name}
                  </span>
                  <span
                    style={{
                      padding: '2px 8px',
                      border: `1px solid ${LEVEL_COLORS[entry.level] || '#008f11'}`,
                      color: LEVEL_COLORS[entry.level] || '#008f11',
                      fontFamily: "'Press Start 2P', monospace",
                      fontSize: '0.4rem',
                      borderRadius: 3,
                    }}
                  >
                    L{entry.level}
                  </span>
                  <span
                    style={{
                      fontFamily: "'Press Start 2P', monospace",
                      fontSize: '0.65rem',
                      color: '#00ff41',
                      minWidth: 28,
                      textAlign: 'right',
                    }}
                  >
                    {Math.round(entry.score)}
                  </span>
                </div>
              ))}
            </div>
          )}
          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
            <button
              style={styles.secondaryButton}
              onClick={() => navigate('/leaderboard')}
            >
              View Full Leaderboard
            </button>
          </div>
        </div>

        <div style={styles.footer}>
          Powered by the PECAM Framework &mdash; Open Source (MIT + CC-BY-SA 4.0)
        </div>
      </div>
    </div>
  )
}
