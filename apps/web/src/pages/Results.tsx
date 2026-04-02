/**
 * Results page: displays final score, level badge, PECAM radar chart, pillar breakdown.
 * Includes claim form (register/login) to generate badge.
 * Matrix green theme with glow animations.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import RadarChart, { PILLAR_LABELS } from '../components/RadarChart'
import PaywallModal from '../components/PaywallModal'
import AuthModal from '../components/AuthModal'
import { useAuth } from '../contexts/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface PillarData {
  kba: number
  ppa: number
  combined: number
}

interface ResultsData {
  assessment_id: string
  mode: string
  status: string
  results_locked: boolean
  final_score: number
  level: number
  kba_score: number
  ppa_score: number
  psv_score: number | null
  pillar_scores: Record<string, PillarData>
  completed_at: string
}

interface ResultsProps {
  assessmentId: string
  mode: string
}

const LEVEL_LABELS: Record<number, string> = {
  1: 'NOVICE',
  2: 'PRACTITIONER',
  3: 'PROFICIENT',
  4: 'EXPERT',
  5: 'MASTER',
}

const LEVEL_COLORS: Record<number, string> = {
  1: '#666666',
  2: '#008f11',
  3: '#00ff41',
  4: '#6D5FFA',
  5: '#EC41FB',
}

const styles = {
  container: {
    maxWidth: 700,
    margin: '0 auto',
    padding: '2rem 1rem',
  },
  title: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '1rem',
    color: '#00ff41',
    textAlign: 'center' as const,
    marginBottom: '2rem',
    textShadow: '0 0 20px rgba(0,255,65,0.4)',
  },
  scoreCard: {
    textAlign: 'center' as const,
    padding: '2rem',
    border: '1px solid rgba(0,255,65,0.2)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.6)',
    marginBottom: '2rem',
    boxShadow: '0 0 30px rgba(0,255,65,0.1)',
  },
  scoreLabel: {
    fontSize: '0.85rem',
    color: '#008f11',
    marginBottom: '0.5rem',
    textTransform: 'uppercase' as const,
    letterSpacing: '2px',
  },
  scoreValue: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '3rem',
    color: '#00ff41',
    textShadow: '0 0 40px rgba(0,255,65,0.5)',
    marginBottom: '0.5rem',
  },
  levelBadge: {
    display: 'inline-block',
    padding: '8px 20px',
    borderRadius: 4,
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.7rem',
    letterSpacing: '2px',
    marginTop: '1rem',
  },
  sectionTitle: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.65rem',
    color: '#008f11',
    marginBottom: '1rem',
    textTransform: 'uppercase' as const,
    letterSpacing: '2px',
  },
  radarSection: {
    padding: '1.5rem',
    border: '1px solid rgba(0,255,65,0.15)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.4)',
    marginBottom: '2rem',
  },
  breakdownGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  },
  breakdownCard: {
    padding: '1rem',
    border: '1px solid rgba(0,255,65,0.15)',
    borderRadius: 4,
    background: 'rgba(0,15,0,0.4)',
    textAlign: 'center' as const,
  },
  breakdownLabel: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.55rem',
    color: '#008f11',
    marginBottom: '0.5rem',
  },
  breakdownValue: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '1rem',
    color: '#00ff41',
  },
  breakdownSub: {
    fontSize: '0.75rem',
    color: '#008f11',
    marginTop: '0.25rem',
  },
  phaseScores: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  },
  phaseCard: {
    padding: '1rem',
    border: '1px solid rgba(0,255,65,0.12)',
    borderRadius: 4,
    background: 'rgba(0,15,0,0.3)',
    textAlign: 'center' as const,
  },
  phaseLabel: {
    fontSize: '0.8rem',
    color: '#008f11',
    marginBottom: '0.3rem',
  },
  phaseValue: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '1.2rem',
    color: '#00ff41',
  },
  loading: {
    textAlign: 'center' as const,
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.8rem',
    color: '#00ff41',
    padding: '4rem',
  },
  error: {
    textAlign: 'center' as const,
    color: '#ff4444',
    padding: '2rem',
    fontSize: '0.9rem',
  },
  mode: {
    fontSize: '0.75rem',
    color: '#008f11',
    textTransform: 'uppercase' as const,
    letterSpacing: '3px',
    marginBottom: '0.3rem',
  },
  // Claim form styles
  claimSection: {
    padding: '2rem',
    border: '1px solid rgba(0,255,65,0.2)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.6)',
    marginTop: '2rem',
  },
  claimTitle: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.7rem',
    color: '#00ff41',
    textAlign: 'center' as const,
    marginBottom: '1.5rem',
    textShadow: '0 0 10px rgba(0,255,65,0.3)',
  },
  input: {
    width: '100%',
    padding: '10px 14px',
    border: '1px solid rgba(0,255,65,0.2)',
    borderRadius: 4,
    background: 'rgba(0,15,0,0.8)',
    color: '#c0ffc0',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '0.9rem',
    marginBottom: '0.75rem',
    outline: 'none',
    boxSizing: 'border-box' as const,
  },
  claimButton: {
    width: '100%',
    padding: '12px',
    borderRadius: 4,
    border: 'none',
    background: 'linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 40%, #EC41FB 100%)',
    color: '#ffffff',
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.6rem',
    cursor: 'pointer',
    letterSpacing: '1px',
    marginTop: '0.5rem',
  },
  toggleLink: {
    display: 'block',
    textAlign: 'center' as const,
    color: '#008f11',
    fontSize: '0.8rem',
    cursor: 'pointer',
    marginTop: '1rem',
    textDecoration: 'underline',
    background: 'none',
    border: 'none',
    fontFamily: "'Share Tech Mono', monospace",
  },
  claimError: {
    color: '#ff4444',
    fontSize: '0.8rem',
    textAlign: 'center' as const,
    marginTop: '0.5rem',
  },
  claimSuccess: {
    textAlign: 'center' as const,
    padding: '2rem',
    border: '1px solid rgba(0,255,65,0.3)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.6)',
    marginTop: '2rem',
  },
  badgeLink: {
    display: 'inline-block',
    padding: '10px 24px',
    borderRadius: 4,
    background: 'linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 40%, #EC41FB 100%)',
    color: '#ffffff',
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.55rem',
    textDecoration: 'none',
    letterSpacing: '1px',
    marginTop: '1rem',
    cursor: 'pointer',
  },
  ctaSection: {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'center',
    marginTop: '2rem',
    flexWrap: 'wrap' as const,
  },
  ctaButton: {
    padding: '12px 24px',
    borderRadius: 4,
    border: '1px solid rgba(0,255,65,0.3)',
    background: 'rgba(0,15,0,0.6)',
    color: '#00ff41',
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.55rem',
    cursor: 'pointer',
    letterSpacing: '1px',
    textDecoration: 'none',
    display: 'inline-block',
  },
}

export default function Results({ assessmentId, mode: _mode }: ResultsProps) {
  const navigate = useNavigate()
  const { token, isAuthenticated } = useAuth()
  const [results, setResults] = useState<ResultsData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [scoreAnimated, setScoreAnimated] = useState(0)
  const [showPaywall, setShowPaywall] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const res = await fetch(`${API_URL}/assessments/${assessmentId}/results`)
        if (!res.ok) {
          const data = await res.json()
          throw new Error(data.detail || 'Failed to fetch results')
        }
        const data: ResultsData = await res.json()
        setResults(data)

        // Show paywall if results are locked
        if (data.results_locked) {
          setShowPaywall(true)
          setLoading(false)
          return
        }

        // Animate score from 0 to final
        const target = Math.round(data.final_score)
        let current = 0
        const step = Math.max(1, Math.floor(target / 40))
        const interval = setInterval(() => {
          current += step
          if (current >= target) {
            current = target
            clearInterval(interval)
          }
          setScoreAnimated(current)
        }, 30)

        return () => clearInterval(interval)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }
    fetchResults()
  }, [assessmentId])

  useEffect(() => {
    if (!isAuthenticated || !token) return
    if (!results || results.results_locked) return

    const autoClaim = async () => {
      try {
        const res = await fetch(`${API_URL}/assessments/${assessmentId}/claim`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        })

        if (!res.ok && res.status !== 409) {
          // 409 means already claimed, which is fine
          console.error('Auto-claim failed')
        } else {
          // Successfully claimed, navigate to dashboard
          navigate('/dashboard')
        }
      } catch (err) {
        // Silently fail for auto-claim
        console.error('Auto-claim error:', err)
      }
    }

    void autoClaim()
  }, [assessmentId, isAuthenticated, results, token, navigate])

  if (loading) {
    return <div style={styles.loading}>[ COMPUTING RESULTS... ]</div>
  }

  if (error || !results) {
    return <div style={styles.error}>{error || 'Failed to load results'}</div>
  }

  // Show paywall if results are locked
  if (results.results_locked) {
    return (
      <>
        <div style={styles.container}>
          <div style={styles.title}>ASSESSMENT COMPLETE</div>
          <div style={styles.scoreCard}>
            <div style={styles.mode}>{results.mode} mode</div>
            <div style={styles.scoreLabel}>Your results are ready!</div>
            <div style={{ fontSize: '1rem', color: '#008f11', marginTop: '1rem' }}>
              Upgrade to Premium to unlock your full assessment results
            </div>
          </div>
        </div>
        <PaywallModal
          isOpen={showPaywall}
          onClose={() => setShowPaywall(false)}
          onUpgrade={() => {
            window.location.href = '/pricing'
          }}
        />
      </>
    )
  }

  const levelColor = LEVEL_COLORS[results.level] || '#00ff41'
  const levelLabel = LEVEL_LABELS[results.level] || 'UNKNOWN'

  return (
    <div style={styles.container}>
      <div style={styles.title}>ASSESSMENT COMPLETE</div>

      {/* Final Score Card */}
      <div style={styles.scoreCard}>
        <div style={styles.mode}>{results.mode} mode</div>
        <div style={styles.scoreLabel}>Final Score</div>
        <div style={styles.scoreValue}>{scoreAnimated}</div>
        <div
          style={{
            ...styles.levelBadge,
            color: levelColor,
            border: `2px solid ${levelColor}`,
            background: `${levelColor}15`,
            textShadow: `0 0 10px ${levelColor}60`,
          }}
        >
          L{results.level} - {levelLabel}
        </div>
      </div>

      {/* Phase Scores */}
      <div style={styles.sectionTitle}>Phase Scores</div>
      <div style={styles.phaseScores}>
        <div style={styles.phaseCard}>
          <div style={styles.phaseLabel}>KBA (Knowledge)</div>
          <div style={styles.phaseValue}>{Math.round(results.kba_score)}</div>
        </div>
        <div style={styles.phaseCard}>
          <div style={styles.phaseLabel}>PPA (Practical)</div>
          <div style={styles.phaseValue}>{Math.round(results.ppa_score)}</div>
        </div>
        {results.psv_score !== null && (
          <div style={styles.phaseCard}>
            <div style={styles.phaseLabel}>PSV (Portfolio)</div>
            <div style={styles.phaseValue}>{Math.round(results.psv_score)}</div>
          </div>
        )}
      </div>

      {/* PECAM Radar Chart */}
      <div style={styles.radarSection}>
        <div style={styles.sectionTitle}>PECAM Pillar Analysis</div>
        <RadarChart pillarScores={results.pillar_scores} size={300} />
      </div>

      {/* Pillar Breakdown */}
      <div style={styles.sectionTitle}>Pillar Breakdown</div>
      <div style={styles.breakdownGrid}>
        {Object.entries(results.pillar_scores).map(([pillar, data]) => (
          <div key={pillar} style={styles.breakdownCard}>
            <div style={styles.breakdownLabel}>{pillar}</div>
            <div style={styles.breakdownValue}>{Math.round(data.combined)}%</div>
            <div style={styles.breakdownSub}>
              {PILLAR_LABELS[pillar] || pillar}
            </div>
            <div style={{ ...styles.breakdownSub, fontSize: '0.65rem' }}>
              KBA: {Math.round(data.kba)} | PPA: {Math.round(data.ppa)}
            </div>
          </div>
        ))}
      </div>

      {/* Claim Section */}
      {isAuthenticated ? (
        <div style={styles.claimSuccess}>
          <div style={styles.sectionTitle}>Assessment Complete!</div>
          <p style={{ color: '#00ff41', fontSize: '0.9rem', marginTop: '1rem' }}>
            Your badge has been saved to your dashboard
          </p>
          <div style={styles.ctaSection}>
            {results.mode === 'full' && (
              <button onClick={() => navigate('/leaderboard')} style={styles.ctaButton}>
                View Leaderboard
              </button>
            )}
            <button onClick={() => navigate('/dashboard')} style={styles.ctaButton}>
              Back to Dashboard
            </button>
          </div>
        </div>
      ) : (
        <div style={styles.claimSection}>
          <div style={styles.claimTitle}>Sign in to save your badge</div>
          <p style={{ color: '#008f11', fontSize: '0.8rem', marginTop: '1rem' }}>
            Create an account to track your progress and claim your achievement badge
          </p>
          <button
            onClick={() => setShowAuthModal(true)}
            style={styles.ctaButton}
          >
            Sign In
          </button>
        </div>
      )}

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        mode="signin"
        intent="dashboard"
      />
    </div>
  )
}
