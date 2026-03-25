/**
 * TabLock overlay: displays a warning when a tab switch violation is detected.
 * Semi-transparent overlay with matrix theme. Does not fully block the page.
 */

interface TabLockProps {
  visible: boolean
  violations: number
  maxViolations?: number
  isVoided: boolean
  onDismiss: () => void
}

const styles = {
  overlay: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.85)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
    backdropFilter: 'blur(4px)',
  },
  card: {
    maxWidth: 480,
    padding: '2.5rem',
    border: '2px solid rgba(255,68,68,0.5)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.95)',
    textAlign: 'center' as const,
    boxShadow: '0 0 40px rgba(255,68,68,0.2)',
  },
  voidedCard: {
    maxWidth: 480,
    padding: '2.5rem',
    border: '2px solid #ff4444',
    borderRadius: 8,
    background: 'rgba(30,0,0,0.95)',
    textAlign: 'center' as const,
    boxShadow: '0 0 60px rgba(255,68,68,0.3)',
  },
  icon: {
    fontSize: '2.5rem',
    marginBottom: '1rem',
  },
  title: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.85rem',
    color: '#ff4444',
    marginBottom: '1rem',
    textShadow: '0 0 10px rgba(255,68,68,0.4)',
  },
  message: {
    color: '#c0ffc0',
    fontSize: '0.9rem',
    lineHeight: 1.6,
    marginBottom: '1.5rem',
    fontFamily: "'Share Tech Mono', monospace",
  },
  counter: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.7rem',
    color: '#ff4444',
    marginBottom: '1.5rem',
  },
  button: {
    padding: '10px 28px',
    borderRadius: 4,
    border: '1px solid rgba(0,255,65,0.3)',
    background: 'rgba(0,15,0,0.6)',
    color: '#00ff41',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '0.9rem',
    cursor: 'pointer',
  },
}

export default function TabLock({
  visible,
  violations,
  maxViolations = 3,
  isVoided,
  onDismiss,
}: TabLockProps) {
  if (!visible && !isVoided) return null

  if (isVoided) {
    return (
      <div style={styles.overlay}>
        <div style={styles.voidedCard}>
          <div style={styles.title}>[ SESSION VOIDED ]</div>
          <div style={styles.message}>
            Your assessment has been voided due to {maxViolations} integrity violations.
            <br />
            This session can no longer be completed.
          </div>
          <button
            style={{
              ...styles.button,
              borderColor: 'rgba(255,68,68,0.3)',
              color: '#ff4444',
            }}
            onClick={() => window.location.href = '/'}
          >
            Return Home
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.overlay} onClick={onDismiss}>
      <div style={styles.card} onClick={(e) => e.stopPropagation()}>
        <div style={styles.title}>[ TAB SWITCH DETECTED ]</div>
        <div style={styles.message}>
          Leaving the assessment tab has been recorded as an integrity violation.
          <br />
          Please remain on this page during the assessment.
        </div>
        <div style={styles.counter}>
          VIOLATIONS: {violations} / {maxViolations}
        </div>
        <button style={styles.button} onClick={onDismiss}>
          Continue Assessment
        </button>
      </div>
    </div>
  )
}
