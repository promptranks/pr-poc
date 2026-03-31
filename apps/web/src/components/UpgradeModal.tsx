import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

interface UpgradeModalProps {
  isOpen: boolean
  onClose: () => void
}

type BillingPlan = 'premium_monthly' | 'premium_annual'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const PRIMARY_GRADIENT = 'linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 50%, #EC41FB 100%)'

const PLAN_DETAILS: Record<BillingPlan, { label: string; price: string; period: string; note: string }> = {
  premium_monthly: {
    label: 'Monthly',
    price: '$19',
    period: '/month',
    note: 'Flexible monthly access for premium assessments and analytics.',
  },
  premium_annual: {
    label: 'Annual',
    price: '$190',
    period: '/year',
    note: 'Best value for long-term premium access with one annual billing cycle.',
  },
}

const FEATURES = [
  '3 full assessments per month',
  'Industry & role targeting',
  'Advanced analytics dashboard',
  'Priority support',
]

export default function UpgradeModal({ isOpen, onClose }: UpgradeModalProps) {
  const { token } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [plan, setPlan] = useState<BillingPlan>('premium_monthly')

  if (!isOpen) return null

  const handleUpgrade = async () => {
    if (!token) {
      setError('Please sign in again before starting checkout.')
      return
    }

    setLoading(true)
    setError('')

    sessionStorage.setItem('pending_subscription_plan', plan)
    sessionStorage.setItem('pending_subscription_upgrade', 'true')

    try {
      const response = await fetch(`${API_URL}/payments/create-checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ plan }),
      })

      const data = await response.json().catch(() => null)

      if (!response.ok) {
        setError(data?.detail || 'Checkout is not ready yet. Please finish Stripe setup and try again.')
        return
      }

      if (!data?.checkout_url) {
        setError('Checkout is not ready yet. Please finish Stripe setup and try again.')
        return
      }

      window.location.href = data.checkout_url
    } catch {
      setError('Unable to reach the payment service right now. Please verify Stripe setup and API connectivity.')
    } finally {
      setLoading(false)
    }
  }

  const selectedPlan = PLAN_DETAILS[plan]

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <button style={styles.close} onClick={onClose} aria-label="Close upgrade modal">×</button>

        <div style={styles.headerGlow} />

        <div style={styles.content}>
          <div style={styles.badge}>PREMIUM ACCESS</div>
          <h2 style={styles.title}>Upgrade to Premium</h2>
          <p style={styles.subtitle}>Unlock full assessments, targeted role tracks, and deeper analytics.</p>

          <div style={styles.planRow}>
            {(Object.keys(PLAN_DETAILS) as BillingPlan[]).map((planKey) => {
              const option = PLAN_DETAILS[planKey]
              const active = planKey === plan
              return (
                <button
                  key={planKey}
                  type="button"
                  style={{
                    ...styles.planOption,
                    ...(active ? styles.planOptionActive : {}),
                  }}
                  onClick={() => setPlan(planKey)}
                >
                  <div style={styles.planLabel}>{option.label}</div>
                  <div style={styles.planValue}>{option.price}<span style={styles.planPeriod}>{option.period}</span></div>
                </button>
              )
            })}
          </div>

          <div style={styles.pricingCard}>
            <div style={styles.priceRow}>
              <span style={styles.price}>{selectedPlan.price}</span>
              <span style={styles.period}>{selectedPlan.period}</span>
            </div>
            <p style={styles.pricingNote}>{selectedPlan.note}</p>
          </div>

          <div style={styles.features}>
            {FEATURES.map((feature) => (
              <div key={feature} style={styles.featureRow}>
                <span style={styles.check}>✓</span>
                <span style={styles.featureText}>{feature}</span>
              </div>
            ))}
          </div>

          {error && <div style={styles.error}>{error}</div>}

          <button
            style={{ ...styles.upgradeBtn, ...(loading ? styles.disabledBtn : {}) }}
            onClick={handleUpgrade}
            disabled={loading}
          >
            {loading ? 'Preparing secure checkout...' : `Upgrade ${plan === 'premium_monthly' ? 'Monthly' : 'Annual'}`}
          </button>

          <p style={styles.footerNote}>You’ll be redirected to Stripe Checkout to complete payment securely.</p>
        </div>
      </div>
    </div>
  )
}

const styles = {
  overlay: {
    position: 'fixed' as const,
    inset: 0,
    background: 'rgba(3, 7, 18, 0.82)',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1.25rem',
    zIndex: 1000,
  },
  modal: {
    width: '100%',
    maxWidth: '540px',
    position: 'relative' as const,
    borderRadius: '28px',
    overflow: 'hidden',
    background: 'linear-gradient(180deg, rgba(17,20,40,0.96) 0%, rgba(10,7,20,0.98) 100%)',
    border: '1px solid rgba(255,255,255,0.1)',
    boxShadow: '0 28px 80px rgba(0,0,0,0.45)',
    color: '#F8FAFC',
  },
  headerGlow: {
    position: 'absolute' as const,
    top: '-80px',
    right: '-30px',
    width: '220px',
    height: '220px',
    borderRadius: '999px',
    background: 'radial-gradient(circle, rgba(236,65,251,0.28) 0%, rgba(236,65,251,0) 72%)',
    pointerEvents: 'none' as const,
  },
  close: {
    position: 'absolute' as const,
    top: '16px',
    right: '18px',
    width: '36px',
    height: '36px',
    borderRadius: '999px',
    border: '1px solid rgba(255,255,255,0.12)',
    background: 'rgba(255,255,255,0.06)',
    color: '#F8FAFC',
    fontSize: '22px',
    lineHeight: 1,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    padding: '32px 30px 28px',
    position: 'relative' as const,
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '0.4rem 0.75rem',
    borderRadius: '999px',
    border: '1px solid rgba(109,95,250,0.35)',
    background: 'rgba(109,95,250,0.16)',
    color: '#C4B5FD',
    fontSize: '0.75rem',
    fontWeight: 800,
    letterSpacing: '0.08em',
    marginBottom: '1rem',
  },
  title: {
    fontSize: '2rem',
    lineHeight: 1.05,
    margin: '0 0 0.75rem',
    fontWeight: 900 as const,
    letterSpacing: '-0.03em',
    textAlign: 'center' as const,
  },
  subtitle: {
    margin: '0 auto 1.5rem',
    maxWidth: '420px',
    fontSize: '1rem',
    lineHeight: 1.65,
    color: '#CBD5E1',
    textAlign: 'center' as const,
  },
  planRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
    gap: '0.75rem',
    marginBottom: '1.25rem',
  },
  planOption: {
    padding: '0.95rem 1rem',
    borderRadius: '18px',
    border: '1px solid rgba(255,255,255,0.08)',
    background: 'rgba(255,255,255,0.04)',
    color: '#CBD5E1',
    cursor: 'pointer',
    textAlign: 'left' as const,
  },
  planOptionActive: {
    border: '1px solid rgba(109,95,250,0.45)',
    background: 'rgba(109,95,250,0.16)',
    boxShadow: '0 12px 30px rgba(109,95,250,0.18)',
  },
  planLabel: {
    fontSize: '0.82rem',
    fontWeight: 800,
    color: '#C4B5FD',
    letterSpacing: '0.05em',
    marginBottom: '0.35rem',
    textTransform: 'uppercase' as const,
  },
  planValue: {
    fontSize: '1.35rem',
    fontWeight: 900 as const,
    color: '#F8FAFC',
  },
  planPeriod: {
    marginLeft: '0.2rem',
    fontSize: '0.9rem',
    color: '#CBD5E1',
    fontWeight: 500 as const,
  },
  pricingCard: {
    borderRadius: '20px',
    border: '1px solid rgba(255,255,255,0.08)',
    background: 'rgba(255,255,255,0.05)',
    padding: '1.25rem 1rem',
    marginBottom: '1.25rem',
    textAlign: 'center' as const,
  },
  priceRow: {
    display: 'flex',
    alignItems: 'flex-end',
    justifyContent: 'center',
    gap: '0.35rem',
    marginBottom: '0.35rem',
  },
  price: {
    fontSize: '3.5rem',
    fontWeight: 900 as const,
    lineHeight: 1,
    color: '#F8FAFC',
    letterSpacing: '-0.05em',
  },
  period: {
    fontSize: '1.15rem',
    color: '#CBD5E1',
    paddingBottom: '0.45rem',
  },
  pricingNote: {
    margin: 0,
    fontSize: '0.92rem',
    lineHeight: 1.55,
    color: '#94A3B8',
  },
  features: {
    display: 'grid',
    gap: '0.75rem',
    marginBottom: '1.25rem',
  },
  featureRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.85rem 0.95rem',
    borderRadius: '16px',
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.06)',
  },
  check: {
    width: '24px',
    height: '24px',
    borderRadius: '999px',
    background: 'rgba(16,185,129,0.18)',
    border: '1px solid rgba(16,185,129,0.4)',
    color: '#6EE7B7',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.9rem',
    fontWeight: 800 as const,
    flexShrink: 0,
  },
  featureText: {
    fontSize: '0.98rem',
    color: '#E2E8F0',
    lineHeight: 1.5,
  },
  upgradeBtn: {
    width: '100%',
    padding: '16px 18px',
    border: 'none',
    borderRadius: '16px',
    background: PRIMARY_GRADIENT,
    color: '#FFFFFF',
    fontSize: '1rem',
    fontWeight: 800 as const,
    cursor: 'pointer',
    boxShadow: '0 18px 40px rgba(109,95,250,0.32)',
  },
  disabledBtn: {
    opacity: 0.7,
    cursor: 'not-allowed',
  },
  error: {
    padding: '0.95rem 1rem',
    borderRadius: '14px',
    marginBottom: '1rem',
    background: 'rgba(127, 29, 29, 0.32)',
    border: '1px solid rgba(248, 113, 113, 0.35)',
    color: '#FECACA',
    textAlign: 'center' as const,
    lineHeight: 1.5,
    fontSize: '0.92rem',
  },
  footerNote: {
    margin: '0.9rem 0 0',
    textAlign: 'center' as const,
    fontSize: '0.82rem',
    lineHeight: 1.5,
    color: '#94A3B8',
  },
}
