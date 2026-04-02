import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import RadarChart, { PILLAR_LABELS } from '../components/RadarChart'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface AssessmentDetail {
  assessment: {
    id: string
    mode: string
    final_score: number
    level: number
    status: string
    completed_at: string
    industry: string | null
    role: string | null
  }
  pillar_scores: Record<string, Record<string, number>>
  recommendations: Array<{ pillar: string; title: string; description: string }>
}

const LEVEL_NAMES: Record<number, string> = {
  1: 'NOVICE',
  2: 'INTERMEDIATE',
  3: 'PROFICIENT',
  4: 'ADVANCED',
  5: 'EXPERT',
}

const LEVEL_COLORS: Record<number, string> = {
  1: '#64748B',
  2: '#10B981',
  3: '#3BB9FB',
  4: '#8B5CF6',
  5: '#EC41FB',
}

export default function AssessmentDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { token } = useAuth()
  const [data, setData] = useState<AssessmentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token || !id) {
      navigate('/dashboard')
      return
    }

    const fetchDetail = async () => {
      try {
        const res = await fetch(`${API_URL}/dashboard/assessments/${id}/details`, {
          headers: { Authorization: `Bearer ${token}` },
        })

        if (!res.ok) {
          throw new Error('Failed to load assessment details')
        }

        const result = await res.json()
        setData(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchDetail()
  }, [id, token, navigate])

  if (loading) {
    return <div style={styles.page}>[ LOADING... ]</div>
  }

  if (error || !data) {
    return (
      <div style={styles.page}>
        <div style={styles.error}>Error: {error || 'No data'}</div>
        <button onClick={() => navigate('/dashboard')} style={styles.backButton}>
          Back to Dashboard
        </button>
      </div>
    )
  }

  const { assessment, pillar_scores } = data

  // Convert pillar_scores to RadarChart format
  const radarPillarScores: Record<string, { kba: number; ppa: number; combined: number }> = {}
  Object.entries(pillar_scores).forEach(([pillar, scores]) => {
    radarPillarScores[pillar] = {
      kba: scores.kba || 0,
      ppa: scores.ppa || 0,
      combined: scores.combined || 0,
    }
  })

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <button onClick={() => navigate('/dashboard')} style={styles.backButton}>
          ← Back to Dashboard
        </button>
        <h1 style={styles.title}>Assessment Details</h1>
      </div>

      <div style={styles.card}>
        <div style={styles.scoreSection}>
          <div style={styles.scoreCircle}>
            <div style={{ ...styles.scoreValue, color: LEVEL_COLORS[assessment.level] }}>
              {Math.round(assessment.final_score)}
            </div>
            <div style={styles.scoreLabel}>OVERALL SCORE</div>
          </div>
          <div style={styles.levelBadge}>
            <div style={styles.levelLabel}>Level {assessment.level}</div>
            <div style={{ ...styles.levelName, color: LEVEL_COLORS[assessment.level] }}>
              {LEVEL_NAMES[assessment.level]}
            </div>
          </div>
        </div>

        <div style={styles.metadata}>
          <div style={styles.metaItem}>
            <span style={styles.metaLabel}>Mode:</span>
            <span style={styles.metaValue}>{assessment.mode === 'quick' ? 'Quick' : 'Full'}</span>
          </div>
          <div style={styles.metaItem}>
            <span style={styles.metaLabel}>Completed:</span>
            <span style={styles.metaValue}>
              {new Date(assessment.completed_at).toLocaleDateString()}
            </span>
          </div>
          {assessment.industry && (
            <div style={styles.metaItem}>
              <span style={styles.metaLabel}>Industry:</span>
              <span style={styles.metaValue}>{assessment.industry}</span>
            </div>
          )}
          {assessment.role && (
            <div style={styles.metaItem}>
              <span style={styles.metaLabel}>Role:</span>
              <span style={styles.metaValue}>{assessment.role}</span>
            </div>
          )}
        </div>
      </div>

      <div style={styles.card}>
        <h2 style={styles.sectionTitle}>PECAM Pillar Analysis</h2>
        <div style={styles.radarContainer}>
          <RadarChart pillarScores={radarPillarScores} />
        </div>
        <div style={styles.pillarBreakdown}>
          {Object.entries(pillar_scores).map(([pillar, scores]) => (
            <div key={pillar} style={styles.pillarItem}>
              <div style={styles.pillarHeader}>
                <span style={styles.pillarName}>{pillar}</span>
                <span style={styles.pillarLabel}>{PILLAR_LABELS[pillar]}</span>
              </div>
              <div style={styles.pillarScore}>{Math.round(scores.combined || 0)}%</div>
            </div>
          ))}
        </div>
      </div>

      {data.recommendations && data.recommendations.length > 0 && (
        <div style={styles.card}>
          <h2 style={styles.sectionTitle}>Recommendations</h2>
          {data.recommendations.map((rec, idx) => (
            <div key={idx} style={styles.recommendation}>
              <div style={styles.recTitle}>{rec.title}</div>
              <div style={styles.recDescription}>{rec.description}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    backgroundColor: '#0a0a0a',
    color: '#00ff41',
    padding: '2rem',
    fontFamily: "'Courier New', monospace",
  },
  header: {
    marginBottom: '2rem',
  },
  backButton: {
    background: 'transparent',
    border: '1px solid #00ff41',
    color: '#00ff41',
    padding: '0.5rem 1rem',
    cursor: 'pointer',
    fontFamily: "'Courier New', monospace",
    fontSize: '0.9rem',
    marginBottom: '1rem',
  },
  title: {
    fontSize: '2rem',
    fontWeight: 'bold',
    margin: 0,
  },
  card: {
    backgroundColor: '#1a1a1a',
    border: '1px solid #00ff41',
    padding: '2rem',
    marginBottom: '2rem',
    borderRadius: '4px',
  },
  scoreSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '3rem',
    marginBottom: '2rem',
  },
  scoreCircle: {
    textAlign: 'center' as const,
  },
  scoreValue: {
    fontSize: '4rem',
    fontWeight: 'bold',
  },
  scoreLabel: {
    fontSize: '0.8rem',
    color: '#008f11',
    marginTop: '0.5rem',
  },
  levelBadge: {
    textAlign: 'center' as const,
  },
  levelLabel: {
    fontSize: '0.9rem',
    color: '#008f11',
  },
  levelName: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    marginTop: '0.5rem',
  },
  metadata: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
  },
  metaItem: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.25rem',
  },
  metaLabel: {
    fontSize: '0.8rem',
    color: '#008f11',
  },
  metaValue: {
    fontSize: '1rem',
    color: '#00ff41',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    marginBottom: '1.5rem',
    color: '#00ff41',
  },
  radarContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: '2rem',
  },
  pillarBreakdown: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
  },
  pillarItem: {
    border: '1px solid #00ff41',
    padding: '1rem',
    borderRadius: '4px',
  },
  pillarHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '0.5rem',
  },
  pillarName: {
    fontSize: '1.2rem',
    fontWeight: 'bold',
  },
  pillarLabel: {
    fontSize: '0.8rem',
    color: '#008f11',
  },
  pillarScore: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    color: '#00ff41',
  },
  recommendation: {
    marginBottom: '1.5rem',
    paddingBottom: '1.5rem',
    borderBottom: '1px solid #333',
  },
  recTitle: {
    fontSize: '1.1rem',
    fontWeight: 'bold',
    marginBottom: '0.5rem',
  },
  recDescription: {
    fontSize: '0.9rem',
    color: '#008f11',
    lineHeight: '1.5',
  },
  error: {
    color: '#ff4444',
    marginBottom: '1rem',
  },
}
