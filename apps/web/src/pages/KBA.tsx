import { useState, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Question {
  id: string
  text: string
  options: string[]
  pillar: string
}

interface KBAProps {
  assessmentId: string
  questions: Question[]
  onComplete: (result: KBAResult) => void
}

export interface KBAResult {
  kba_score: number
  total_correct: number
  total_questions: number
  pillar_scores: Record<string, { score: number; correct: number; total: number }>
}

const PILLAR_NAMES: Record<string, string> = {
  P: 'Prompt Design',
  E: 'Evaluation',
  C: 'Context Mgmt',
  M: 'Meta-Cognition',
  A: 'Agentic',
}

const styles = {
  wrapper: {
    maxWidth: 700,
    margin: '0 auto',
    padding: '1rem',
  },
  progress: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
    padding: '0.75rem 1rem',
    border: '1px solid rgba(0,255,65,0.1)',
    borderRadius: 4,
    background: 'rgba(0,15,0,0.4)',
  },
  counter: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.7rem',
    color: '#00ff41',
  },
  pillarBadge: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.65rem',
    padding: '4px 10px',
    borderRadius: 4,
    border: '1px solid rgba(0,255,65,0.3)',
    color: '#00ff41',
    background: 'rgba(0,255,65,0.08)',
  },
  progressBar: {
    width: '100%',
    height: 3,
    background: 'rgba(0,255,65,0.1)',
    borderRadius: 2,
    marginBottom: '2rem',
    overflow: 'hidden' as const,
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #6D5FFA, #EC41FB)',
    borderRadius: 2,
    transition: 'width 0.3s ease',
  },
  card: {
    padding: '2rem',
    border: '1px solid rgba(0,255,65,0.15)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.6)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.8)',
  },
  questionText: {
    fontSize: '1.05rem',
    color: '#c0ffc0',
    lineHeight: 1.7,
    marginBottom: '1.5rem',
  },
  optionButton: {
    display: 'block',
    width: '100%',
    padding: '12px 16px',
    marginBottom: '0.75rem',
    border: '1px solid rgba(0,255,65,0.15)',
    borderRadius: 4,
    background: 'rgba(0,15,0,0.4)',
    color: '#c0ffc0',
    fontSize: '0.95rem',
    fontFamily: "'Share Tech Mono', monospace",
    cursor: 'pointer',
    textAlign: 'left' as const,
    transition: 'all 0.15s',
  },
  optionSelected: {
    border: '1px solid rgba(109,95,250,0.6)',
    background: 'rgba(109,95,250,0.15)',
    color: '#fff',
    boxShadow: '0 0 10px rgba(109,95,250,0.2)',
  },
  nextButton: {
    marginTop: '1.5rem',
    padding: '14px 36px',
    borderRadius: 4,
    border: 'none',
    background: 'linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 40%, #EC41FB 100%)',
    color: '#fff',
    fontSize: '1rem',
    fontFamily: "'Share Tech Mono', monospace",
    fontWeight: 600,
    cursor: 'pointer',
    float: 'right' as const,
  },
  disabled: {
    opacity: 0.4,
    cursor: 'not-allowed',
  },
  submitting: {
    textAlign: 'center' as const,
    padding: '3rem',
    color: '#00ff41',
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.8rem',
  },
  error: {
    color: '#ff4444',
    fontSize: '0.9rem',
    marginBottom: '1rem',
    textAlign: 'center' as const,
  },
}

export default function KBA({ assessmentId, questions, onComplete }: KBAProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const currentQuestion = questions[currentIndex]
  const selectedOption = answers[currentIndex]
  const isLast = currentIndex === questions.length - 1
  const hasAnswer = selectedOption !== undefined

  const submitAll = useCallback(async (finalAnswers: Record<number, number>) => {
    setSubmitting(true)
    setError('')
    try {
      const payload = questions.map((q, i) => ({
        question_id: q.id,
        selected: finalAnswers[i] ?? -1,
      }))

      const res = await fetch(`${API_BASE}/assessments/${assessmentId}/kba/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: payload }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to submit answers')
      }

      const result: KBAResult = await res.json()
      onComplete(result)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Submission failed'
      setError(message)
      setSubmitting(false)
    }
  }, [assessmentId, questions, onComplete])

  const handleSelect = (optionIndex: number) => {
    if (submitting) return
    setAnswers((prev) => ({ ...prev, [currentIndex]: optionIndex }))
  }

  const handleNext = async () => {
    if (!hasAnswer || submitting) return

    if (isLast) {
      await submitAll(answers)
    } else {
      setCurrentIndex((prev) => prev + 1)
    }
  }

  if (submitting) {
    return (
      <div style={styles.submitting}>
        [ SCORING ASSESSMENT... ]
      </div>
    )
  }

  return (
    <div style={styles.wrapper}>
      {error && <p style={styles.error}>{error}</p>}

      <div style={styles.progress}>
        <span style={styles.counter}>
          {currentIndex + 1} / {questions.length}
        </span>
        <span style={styles.pillarBadge}>
          {currentQuestion.pillar} - {PILLAR_NAMES[currentQuestion.pillar] || currentQuestion.pillar}
        </span>
      </div>

      <div style={styles.progressBar}>
        <div
          style={{
            ...styles.progressFill,
            width: `${((currentIndex + 1) / questions.length) * 100}%`,
          }}
        />
      </div>

      <div style={styles.card}>
        <div style={styles.questionText}>{currentQuestion.text}</div>

        {currentQuestion.options.map((option, i) => (
          <button
            key={i}
            style={{
              ...styles.optionButton,
              ...(selectedOption === i ? styles.optionSelected : {}),
            }}
            onClick={() => handleSelect(i)}
          >
            {String.fromCharCode(65 + i)}. {option}
          </button>
        ))}

        <button
          style={{
            ...styles.nextButton,
            ...(!hasAnswer ? styles.disabled : {}),
          }}
          onClick={handleNext}
          disabled={!hasAnswer}
        >
          {isLast ? '[ SUBMIT ]' : '[ NEXT > ]'}
        </button>
        <div style={{ clear: 'both' as const }} />
      </div>
    </div>
  )
}
