/**
 * Badge page: displays badge SVG with share/download buttons.
 * Matrix green theme.
 */

import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface BadgeData {
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
    marginBottom: '2rem',
  },
  badgeContainer: {
    margin: '1rem 0 2rem',
    maxWidth: 420,
    width: '100%',
  },
  actions: {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'center',
    flexWrap: 'wrap' as const,
    marginBottom: '2rem',
  },
  button: {
    padding: '10px 20px',
    borderRadius: 4,
    border: '1px solid rgba(0,255,65,0.2)',
    background: 'rgba(0,15,0,0.6)',
    color: '#00ff41',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '0.85rem',
    cursor: 'pointer',
  },
  ctaButton: {
    padding: '10px 20px',
    borderRadius: 4,
    border: 'none',
    background: 'linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 40%, #EC41FB 100%)',
    color: '#ffffff',
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.55rem',
    cursor: 'pointer',
    letterSpacing: '1px',
  },
  info: {
    textAlign: 'center' as const,
    padding: '1rem',
    border: '1px solid rgba(0,255,65,0.15)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.4)',
    maxWidth: 420,
    width: '100%',
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '0.5rem 0',
    borderBottom: '1px solid rgba(0,255,65,0.08)',
  },
  infoLabel: {
    color: '#008f11',
    fontSize: '0.85rem',
  },
  infoValue: {
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
    color: '#ff4444',
    padding: '2rem',
    fontSize: '0.9rem',
  },
  copied: {
    color: '#00ff41',
    fontSize: '0.8rem',
    textAlign: 'center' as const,
    marginTop: '0.5rem',
  },
}

export default function Badge() {
  const { badgeId } = useParams<{ badgeId: string }>()
  const [badge, setBadge] = useState<BadgeData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const fetchBadge = async () => {
      try {
        const res = await fetch(`${API_URL}/badges/verify/${badgeId}`)
        if (!res.ok) {
          const data = await res.json()
          throw new Error(data.detail || 'Badge not found')
        }
        const data: BadgeData = await res.json()
        setBadge(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }
    fetchBadge()
  }, [badgeId])

  const handleCopyUrl = async () => {
    const url = `${window.location.origin}/verify/${badgeId}`
    await navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownloadSvg = () => {
    if (!badge?.badge_svg) return
    const blob = new Blob([badge.badge_svg], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `promptranks-badge-L${badge.level}.svg`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return <div style={{ ...styles.page, justifyContent: 'center' }}><div style={styles.loading}>[ LOADING BADGE... ]</div></div>
  }

  if (error || !badge) {
    return <div style={{ ...styles.page, justifyContent: 'center' }}><div style={styles.error}>{error || 'Badge not found'}</div></div>
  }

  return (
    <div style={styles.page}>
      <div style={styles.logo}>PROMPTRANKS</div>

      <div style={styles.badgeContainer}>
        <div dangerouslySetInnerHTML={{ __html: badge.badge_svg }} />
      </div>

      <div style={styles.actions}>
        <button style={styles.ctaButton} onClick={handleCopyUrl}>
          Copy Verify URL
        </button>
        <button style={styles.button} onClick={handleDownloadSvg}>
          Download SVG
        </button>
      </div>

      {copied && <div style={styles.copied}>URL copied to clipboard</div>}

      <div style={styles.info}>
        <div style={styles.infoRow}>
          <span style={styles.infoLabel}>Level</span>
          <span style={styles.infoValue}>L{badge.level} - {badge.level_name}</span>
        </div>
        <div style={styles.infoRow}>
          <span style={styles.infoLabel}>Score</span>
          <span style={styles.infoValue}>{Math.round(badge.final_score)}</span>
        </div>
        <div style={styles.infoRow}>
          <span style={styles.infoLabel}>Mode</span>
          <span style={styles.infoValue}>{badge.mode.toUpperCase()}</span>
        </div>
        <div style={{ ...styles.infoRow, borderBottom: 'none' }}>
          <span style={styles.infoLabel}>Issued</span>
          <span style={styles.infoValue}>{new Date(badge.issued_at).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  )
}
