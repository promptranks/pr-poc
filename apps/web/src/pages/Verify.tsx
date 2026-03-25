/**
 * Public verification page: validates a badge and shows its details.
 * Matrix green theme.
 */

import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface VerifyData {
  badge_id: string
  mode: string
  level: number
  level_name: string
  final_score: number
  pillar_scores: Record<string, unknown>
  badge_svg: string
  issued_at: string
  valid: boolean
}

const LEVEL_COLORS: Record<number, string> = {
  1: '#666666',
  2: '#008f11',
  3: '#00ff41',
  4: '#6D5FFA',
  5: '#EC41FB',
}

const styles = {
  page: {
    minHeight: '100vh',
    background: '#000000',
    color: '#c0ffc0',
    fontFamily: "'Share Tech Mono', monospace",
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    padding: '2rem 1rem',
  },
  logo: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.8rem',
    color: '#00ff41',
    textShadow: '0 0 10px rgba(0,255,65,0.3)',
    marginBottom: '0.5rem',
  },
  subtitle: {
    fontSize: '0.85rem',
    color: '#008f11',
    marginBottom: '2rem',
  },
  validBadge: {
    display: 'inline-block',
    padding: '6px 16px',
    borderRadius: 4,
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.6rem',
    letterSpacing: '2px',
    marginBottom: '1.5rem',
  },
  badgeContainer: {
    margin: '1rem 0 2rem',
    maxWidth: 420,
    width: '100%',
  },
  details: {
    padding: '1.5rem',
    border: '1px solid rgba(0,255,65,0.15)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.4)',
    maxWidth: 420,
    width: '100%',
  },
  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '0.5rem 0',
    borderBottom: '1px solid rgba(0,255,65,0.08)',
  },
  detailLabel: {
    color: '#008f11',
    fontSize: '0.85rem',
  },
  detailValue: {
    color: '#00ff41',
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.65rem',
  },
  loading: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.8rem',
    color: '#00ff41',
    padding: '4rem',
  },
  error: {
    textAlign: 'center' as const,
    maxWidth: 500,
    padding: '2rem',
  },
  errorTitle: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.85rem',
    color: '#ff4444',
    marginBottom: '1rem',
  },
  errorText: {
    color: '#c0ffc0',
    fontSize: '0.9rem',
  },
}

export default function Verify() {
  const { badgeId } = useParams<{ badgeId: string }>()
  const [data, setData] = useState<VerifyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const verify = async () => {
      try {
        const res = await fetch(`${API_URL}/badges/verify/${badgeId}`)
        if (!res.ok) {
          const json = await res.json()
          throw new Error(json.detail || 'Verification failed')
        }
        const json: VerifyData = await res.json()
        setData(json)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }
    verify()
  }, [badgeId])

  if (loading) {
    return <div style={{ ...styles.page, justifyContent: 'center' }}><div style={styles.loading}>[ VERIFYING... ]</div></div>
  }

  if (error || !data) {
    return (
      <div style={{ ...styles.page, justifyContent: 'center' }}>
        <div style={styles.error}>
          <div style={styles.errorTitle}>VERIFICATION FAILED</div>
          <div style={styles.errorText}>{error || 'Badge not found'}</div>
        </div>
      </div>
    )
  }

  const levelColor = LEVEL_COLORS[data.level] || '#00ff41'

  return (
    <div style={styles.page}>
      <div style={styles.logo}>PROMPTRANKS</div>
      <div style={styles.subtitle}>Badge Verification</div>

      <div
        style={{
          ...styles.validBadge,
          color: '#00ff41',
          border: '2px solid #00ff41',
          background: 'rgba(0,255,65,0.08)',
          textShadow: '0 0 10px rgba(0,255,65,0.4)',
        }}
      >
        VERIFIED
      </div>

      <div style={styles.badgeContainer}>
        <div dangerouslySetInnerHTML={{ __html: data.badge_svg }} />
      </div>

      <div style={styles.details}>
        <div style={styles.detailRow}>
          <span style={styles.detailLabel}>Status</span>
          <span style={{ ...styles.detailValue, color: '#00ff41' }}>Valid</span>
        </div>
        <div style={styles.detailRow}>
          <span style={styles.detailLabel}>Level</span>
          <span style={{ ...styles.detailValue, color: levelColor }}>L{data.level} - {data.level_name}</span>
        </div>
        <div style={styles.detailRow}>
          <span style={styles.detailLabel}>Score</span>
          <span style={styles.detailValue}>{Math.round(data.final_score)}</span>
        </div>
        <div style={styles.detailRow}>
          <span style={styles.detailLabel}>Mode</span>
          <span style={styles.detailValue}>{data.mode === 'full' ? 'Certified' : 'Estimated'}</span>
        </div>
        <div style={{ ...styles.detailRow, borderBottom: 'none' }}>
          <span style={styles.detailLabel}>Issued</span>
          <span style={styles.detailValue}>{new Date(data.issued_at).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  )
}
