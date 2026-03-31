interface PaywallModalProps {
  isOpen: boolean
  onClose: () => void
  onUpgrade: () => void
}

export default function PaywallModal({ isOpen, onClose, onUpgrade }: PaywallModalProps) {
  if (!isOpen) return null

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <button style={styles.close} onClick={onClose}>×</button>

        <div style={styles.content}>
          <h2 style={styles.title}>🔒 Unlock Your Full Assessment Results</h2>

          <p style={styles.subtitle}>
            You scored [REDACTED] and earned Level [REDACTED]
          </p>

          <div style={styles.features}>
            <p style={styles.feature}>✓ Final score & level badge</p>
            <p style={styles.feature}>✓ PECAM pillar analysis</p>
            <p style={styles.feature}>✓ Personalized recommendations</p>
            <p style={styles.feature}>✓ Shareable certificate</p>
          </div>

          <button style={styles.upgradeBtn} onClick={onUpgrade}>
            Upgrade to Premium - $19/month
          </button>

          <p style={styles.footer}>
            Already have an account? <a href="#" style={styles.link}>Sign In</a>
          </p>
        </div>
      </div>
    </div>
  )
}

const styles = {
  overlay: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    background: 'white',
    borderRadius: '8px',
    width: '500px',
    maxWidth: '90%',
    position: 'relative' as const,
  },
  close: {
    position: 'absolute' as const,
    top: '10px',
    right: '10px',
    background: 'none',
    border: 'none',
    fontSize: '24px',
    cursor: 'pointer',
  },
  content: {
    padding: '40px 30px',
  },
  title: {
    fontSize: '24px',
    marginBottom: '10px',
    textAlign: 'center' as const,
  },
  subtitle: {
    fontSize: '16px',
    color: '#666',
    textAlign: 'center' as const,
    marginBottom: '30px',
  },
  features: {
    marginBottom: '30px',
  },
  feature: {
    fontSize: '16px',
    marginBottom: '10px',
  },
  upgradeBtn: {
    width: '100%',
    padding: '15px',
    background: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    fontWeight: 'bold' as const,
    cursor: 'pointer',
  },
  footer: {
    marginTop: '20px',
    textAlign: 'center' as const,
    fontSize: '14px',
    color: '#666',
  },
  link: {
    color: '#007bff',
    textDecoration: 'none',
  },
}
