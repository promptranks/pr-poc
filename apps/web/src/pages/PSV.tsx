import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// PECAM level definitions (1–5)
const PECAM_LEVELS: Record<number, { name: string; description: string; color: string }> = {
  1: {
    name: 'Novice',
    description: 'Basic awareness; follows simple instructions but lacks independent application.',
    color: '#8B5CF6',
  },
  2: {
    name: 'Practitioner',
    description: 'Applies concepts with guidance; demonstrates functional competence in common scenarios.',
    color: '#6D5FFA',
  },
  3: {
    name: 'Proficient',
    description: 'Independent and consistent application; adapts techniques to varied contexts.',
    color: '#00cc33',
  },
  4: {
    name: 'Expert',
    description: 'Advanced mastery; optimises for quality, efficiency, and nuance across complex tasks.',
    color: '#00ff41',
  },
  5: {
    name: 'Master',
    description: 'Exceptional calibration; defines best practice and operates at the frontier of the field.',
    color: '#c0ffc0',
  },
}

const PILLAR_LABELS: Record<string, string> = {
  P: 'Precision',
  E: 'Efficiency',
  C: 'Creativity',
  A: 'Adaptability',
  M: 'Metacognition',
}

interface PSVSample {
  sample_id: string
  title: string
  pillar: string
  difficulty: number
  task_context: string
  prompt_text: string
  output_text: string
}

interface PSVProps {
  assessmentId: string
  onComplete: () => void
}

export interface PSVResult {
  psv_score: number
  user_level: number
  ground_truth_level: number
  delta: number
}

const styles = {
  wrapper: {
    maxWidth: 1000,
    margin: '0 auto',
    padding: '0.5rem',
  },
  loading: {
    textAlign: 'center' as const,
    padding: '3rem',
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.8rem',
    color: '#00ff41',
  },
  error: {
    color: '#ff4444',
    fontSize: '0.9rem',
    marginBottom: '1rem',
    textAlign: 'center' as const,
    padding: '1rem',
    border: '1px solid rgba(255,68,68,0.3)',
    borderRadius: 4,
    background: 'rgba(255,0,0,0.05)',
  },
  intro: {
    maxWidth: 700,
    margin: '0 auto 1.5rem',
    padding: '1rem 1.5rem',
    border: '1px solid rgba(0,255,65,0.15)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.5)',
    textAlign: 'center' as const,
  },
  introTitle: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.65rem',
    color: '#00ff41',
    marginBottom: '0.6rem',
    letterSpacing: '2px',
  },
  introText: {
    fontSize: '0.85rem',
    color: '#c0ffc0',
    lineHeight: 1.7,
    fontFamily: "'Share Tech Mono', monospace",
  },
  sampleHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
    padding: '0.75rem 1rem',
    border: '1px solid rgba(0,255,65,0.1)',
    borderRadius: 4,
    background: 'rgba(0,15,0,0.4)',
  },
  sampleTitle: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.65rem',
    color: '#00ff41',
    marginBottom: '0.3rem',
  },
  metaBadges: {
    display: 'flex',
    gap: '0.5rem',
    alignItems: 'center',
  },
  badge: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.5rem',
    padding: '3px 8px',
    borderRadius: 3,
    border: '1px solid rgba(0,255,65,0.3)',
    color: '#00ff41',
    background: 'rgba(0,255,65,0.08)',
  },
  difficultyBadge: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.5rem',
    padding: '3px 8px',
    borderRadius: 3,
    border: '1px solid rgba(109,95,250,0.4)',
    color: '#8B5CF6',
    background: 'rgba(109,95,250,0.1)',
  },
  card: {
    padding: '1rem',
    border: '1px solid rgba(0,255,65,0.15)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.6)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.8)',
    marginBottom: '1rem',
  },
  sectionLabel: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.55rem',
    color: '#008f11',
    textTransform: 'uppercase' as const,
    letterSpacing: '2px',
    marginBottom: '0.75rem',
  },
  contextText: {
    fontSize: '0.9rem',
    color: '#c0ffc0',
    lineHeight: 1.7,
    fontFamily: "'Share Tech Mono', monospace",
    whiteSpace: 'pre-wrap' as const,
  },
  codeBlock: {
    padding: '1rem',
    border: '1px solid rgba(0,255,65,0.1)',
    borderRadius: 4,
    background: 'rgba(0,5,0,0.8)',
    fontSize: '0.82rem',
    color: '#c0ffc0',
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap' as const,
    fontFamily: "'Share Tech Mono', monospace",
    overflow: 'auto' as const,
    maxHeight: 240,
  },
  ratingSection: {
    padding: '1.5rem',
    border: '1px solid rgba(0,255,65,0.2)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.6)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.8)',
    marginBottom: '1rem',
  },
  ratingSectionTitle: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.6rem',
    color: '#00ff41',
    marginBottom: '0.4rem',
    letterSpacing: '2px',
  },
  ratingSectionSubtitle: {
    fontSize: '0.82rem',
    color: '#008f11',
    marginBottom: '1.2rem',
    fontFamily: "'Share Tech Mono', monospace",
  },
  levelGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(5, 1fr)',
    gap: '0.6rem',
  },
  levelCard: {
    padding: '0.9rem 0.5rem',
    borderRadius: 6,
    border: '1px solid rgba(0,255,65,0.12)',
    background: 'rgba(0,10,0,0.5)',
    cursor: 'pointer' as const,
    textAlign: 'center' as const,
    transition: 'all 0.15s ease',
    userSelect: 'none' as const,
  },
  levelCardSelected: {
    border: '2px solid #00ff41',
    background: 'rgba(0,255,65,0.1)',
    boxShadow: '0 0 12px rgba(0,255,65,0.2)',
  },
  levelNumber: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '1rem',
    marginBottom: '0.4rem',
  },
  levelName: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.45rem',
    marginBottom: '0.5rem',
    textTransform: 'uppercase' as const,
    letterSpacing: '1px',
  },
  levelDesc: {
    fontSize: '0.72rem',
    color: '#c0ffc0',
    lineHeight: 1.5,
    fontFamily: "'Share Tech Mono', monospace",
  },
  submitButton: {
    width: '100%',
    padding: '14px',
    borderRadius: 4,
    border: 'none',
    background: 'linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 40%, #EC41FB 100%)',
    color: '#fff',
    fontSize: '0.9rem',
    fontFamily: "'Share Tech Mono', monospace",
    fontWeight: 600,
    cursor: 'pointer' as const,
    transition: 'opacity 0.15s',
    marginTop: '0.5rem',
  },
  disabled: {
    opacity: 0.4,
    cursor: 'not-allowed' as const,
  },
  // Post-submit result card
  resultCard: {
    maxWidth: 600,
    margin: '2rem auto',
    padding: '2rem',
    border: '1px solid rgba(0,255,65,0.2)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.6)',
    textAlign: 'center' as const,
    boxShadow: '0 8px 32px rgba(0,0,0,0.8)',
  },
  resultTitle: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.65rem',
    color: '#008f11',
    marginBottom: '0.75rem',
    letterSpacing: '2px',
  },
  scoreDisplay: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '2rem',
    color: '#00ff41',
    textShadow: '0 0 30px rgba(0,255,65,0.4)',
    marginBottom: '0.5rem',
  },
  deltaRow: {
    display: 'flex',
    justifyContent: 'center',
    gap: '2rem',
    margin: '1rem 0',
    flexWrap: 'wrap' as const,
  },
  deltaItem: {
    padding: '0.5rem 1rem',
    border: '1px solid rgba(0,255,65,0.15)',
    borderRadius: 4,
    background: 'rgba(0,10,0,0.4)',
  },
  deltaLabel: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.45rem',
    color: '#008f11',
    marginBottom: '0.3rem',
  },
  deltaValue: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.8rem',
    color: '#00ff41',
  },
  resultSubtext: {
    fontSize: '0.85rem',
    color: '#c0ffc0',
    marginBottom: '1.5rem',
    fontFamily: "'Share Tech Mono', monospace",
    lineHeight: 1.6,
  },
  continueButton: {
    width: '100%',
    padding: '14px',
    borderRadius: 4,
    border: 'none',
    background: 'linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 40%, #EC41FB 100%)',
    color: '#fff',
    fontSize: '0.9rem',
    fontFamily: "'Share Tech Mono', monospace",
    fontWeight: 600,
    cursor: 'pointer' as const,
  },
}

export default function PSV({ assessmentId, onComplete }: PSVProps) {
  const [sample, setSample] = useState<PSVSample | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedLevel, setSelectedLevel] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<PSVResult | null>(null)

  useEffect(() => {
    const fetchSample = async () => {
      try {
        const res = await fetch(`${API_BASE}/assessments/${assessmentId}/psv/sample`)
        if (!res.ok) {
          const data = await res.json()
          throw new Error(data.detail || 'Failed to load PSV sample')
        }
        const data: PSVSample = await res.json()
        setSample(data)
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load PSV sample'
        setError(message)
      } finally {
        setLoading(false)
      }
    }
    fetchSample()
  }, [assessmentId])

  const handleSubmit = async () => {
    if (selectedLevel === null || submitting) return
    setSubmitting(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/assessments/${assessmentId}/psv/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_level: selectedLevel }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Submission failed')
      }
      const data = await res.json()

      // Check if results are locked
      if (data.results_locked) {
        // Show inline message instead of alert
        setError(data.message || '🔒 You are assessing with premium features. Upgrade to Premium to view your score.')
        onComplete()
      } else {
        setResult(data as PSVResult)
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Submission failed'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <div style={styles.loading}>[ LOADING PSV SAMPLE... ]</div>
  }

  if (error && !sample) {
    return <div style={styles.error}>{error}</div>
  }

  // Post-submit result view
  if (result) {
    const deltaLabel =
      result.delta === 0
        ? 'Perfect calibration!'
        : result.delta === 1
        ? 'Off by 1 level — close!'
        : `Off by ${result.delta} levels`

    return (
      <div style={styles.resultCard}>
        <div style={styles.resultTitle}>PSV PHASE COMPLETE</div>
        <div style={styles.scoreDisplay}>{Math.round(result.psv_score)}</div>
        <div style={{ fontSize: '0.82rem', color: '#008f11', marginBottom: '1rem', fontFamily: "'Share Tech Mono', monospace" }}>
          {deltaLabel}
        </div>
        <div style={styles.deltaRow}>
          <div style={styles.deltaItem}>
            <div style={styles.deltaLabel}>YOUR RATING</div>
            <div style={styles.deltaValue}>
              L{result.user_level} — {PECAM_LEVELS[result.user_level]?.name}
            </div>
          </div>
          <div style={styles.deltaItem}>
            <div style={styles.deltaLabel}>GROUND TRUTH</div>
            <div style={styles.deltaValue}>
              L{result.ground_truth_level} — {PECAM_LEVELS[result.ground_truth_level]?.name}
            </div>
          </div>
        </div>
        <div style={styles.resultSubtext}>
          PSV measures your ability to calibrate prompt quality against expert benchmarks.
          Each level off reduces your score by 25 points.
        </div>
        <button style={styles.continueButton} onClick={onComplete}>
          [ VIEW RESULTS ]
        </button>
      </div>
    )
  }

  if (!sample) {
    return <div style={styles.loading}>No PSV sample available</div>
  }

  const pillarLabel = PILLAR_LABELS[sample.pillar] || sample.pillar

  return (
    <div style={styles.wrapper}>
      {error && <div style={styles.error}>{error}</div>}

      {/* Instruction banner */}
      <div style={styles.intro}>
        <div style={styles.introTitle}>PEER SAMPLE VALIDATION</div>
        <div style={styles.introText}>
          Review the prompt and its AI-generated output below. Based on the PECAM framework,
          rate the overall quality of this prompt–output pair on a scale of 1 (Novice) to 5 (Master).
        </div>
      </div>

      {/* Sample header */}
      <div style={styles.sampleHeader}>
        <div>
          <div style={styles.sampleTitle}>{sample.title}</div>
          <div style={styles.metaBadges}>
            <span style={styles.badge}>{pillarLabel}</span>
            <span style={styles.difficultyBadge}>DIFFICULTY {sample.difficulty}</span>
          </div>
        </div>
      </div>

      {/* Task context */}
      <div style={styles.card}>
        <div style={styles.sectionLabel}>Task Context</div>
        <div style={styles.contextText}>{sample.task_context}</div>
      </div>

      {/* Prompt */}
      <div style={styles.card}>
        <div style={styles.sectionLabel}>Prompt Submitted</div>
        <div style={styles.codeBlock}>{sample.prompt_text}</div>
      </div>

      {/* Output */}
      <div style={styles.card}>
        <div style={styles.sectionLabel}>AI-Generated Output</div>
        <div style={styles.codeBlock}>{sample.output_text}</div>
      </div>

      {/* Level selector */}
      <div style={styles.ratingSection}>
        <div style={styles.ratingSectionTitle}>RATE THIS PROMPT</div>
        <div style={styles.ratingSectionSubtitle}>
          Select the PECAM proficiency level that best describes this prompt–output pair:
        </div>
        <div style={styles.levelGrid}>
          {([1, 2, 3, 4, 5] as const).map((level) => {
            const def = PECAM_LEVELS[level]
            const isSelected = selectedLevel === level
            return (
              <div
                key={level}
                style={{
                  ...styles.levelCard,
                  ...(isSelected ? styles.levelCardSelected : {}),
                  borderColor: isSelected ? def.color : undefined,
                  boxShadow: isSelected ? `0 0 12px ${def.color}44` : undefined,
                }}
                onClick={() => setSelectedLevel(level)}
                role="button"
                aria-pressed={isSelected}
                aria-label={`Level ${level}: ${def.name}`}
              >
                <div style={{ ...styles.levelNumber, color: isSelected ? def.color : '#008f11' }}>
                  {level}
                </div>
                <div style={{ ...styles.levelName, color: isSelected ? def.color : '#008f11' }}>
                  {def.name}
                </div>
                <div style={styles.levelDesc}>{def.description}</div>
              </div>
            )
          })}
        </div>

        <button
          style={{
            ...styles.submitButton,
            ...(selectedLevel === null || submitting ? styles.disabled : {}),
          }}
          onClick={handleSubmit}
          disabled={selectedLevel === null || submitting}
        >
          {submitting
            ? '[ SUBMITTING... ]'
            : selectedLevel !== null
            ? `[ SUBMIT RATING: L${selectedLevel} — ${PECAM_LEVELS[selectedLevel].name.toUpperCase()} ]`
            : '[ SELECT A LEVEL TO SUBMIT ]'}
        </button>
      </div>
    </div>
  )
}
