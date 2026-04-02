import { useAuth } from '../contexts/AuthContext'

type BillingPlan = 'premium_monthly' | 'premium_annual'

interface SubscriptionCardProps {
  tier: string
  plan?: string
}

export default function SubscriptionCard({ tier, plan }: SubscriptionCardProps) {
  const { token } = useAuth()
  const normalizedPlan: BillingPlan | null = plan === 'premium_annual' || plan === 'premium_monthly' ? plan : null
  const premiumDescription = normalizedPlan === 'premium_annual'
    ? 'Premium Plan - $190/year'
    : 'Premium Plan - $19/month'

  const handleManage = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/payments/create-portal`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok) {
        const { portal_url } = await response.json()
        window.location.href = portal_url
      }
    } catch (error) {
      console.error('Failed to create portal session:', error)
    }
  }

  return (
    <div style={styles.card}>
      <h3 style={styles.title}>Subscription</h3>
      <div style={styles.tierBadge}>{tier}</div>

      {tier === 'premium' && (
        <>
          <p style={styles.description}>{premiumDescription}</p>
          <button style={styles.button} onClick={handleManage}>
            Manage Subscription
          </button>
        </>
      )}

      {tier === 'free' && (
        <p style={styles.description}>Free Plan - Upgrade to unlock full assessments</p>
      )}
    </div>
  )
}

const styles = {
  card: {
    background: '#1a1a1a',
    padding: '1.5rem',
    borderRadius: '4px',
    border: '1px solid #00ff41',
    marginTop: '2rem',
    fontFamily: "'Courier New', monospace",
  },
  title: {
    fontSize: '1.5rem',
    marginBottom: '1rem',
    color: '#00ff41',
    fontWeight: 'bold' as const,
  },
  tierBadge: {
    display: 'inline-block',
    padding: '0.5rem 1rem',
    background: 'transparent',
    color: '#00ff41',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    fontSize: '0.8rem',
    textTransform: 'uppercase' as const,
    marginBottom: '1rem',
  },
  description: {
    fontSize: '1rem',
    color: '#008f11',
    marginBottom: '1rem',
  },
  button: {
    padding: '0.75rem 1.5rem',
    background: 'transparent',
    color: '#00ff41',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    fontSize: '0.9rem',
    cursor: 'pointer',
    fontFamily: "'Courier New', monospace",
    fontWeight: 'bold' as const,
  },
}
