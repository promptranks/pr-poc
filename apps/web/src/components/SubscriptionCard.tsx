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
    background: '#f8f9fa',
    padding: '20px',
    borderRadius: '8px',
    marginTop: '20px',
  },
  title: {
    fontSize: '20px',
    marginBottom: '10px',
  },
  tierBadge: {
    display: 'inline-block',
    padding: '6px 12px',
    background: '#007bff',
    color: 'white',
    borderRadius: '4px',
    fontSize: '14px',
    textTransform: 'uppercase' as const,
    marginBottom: '15px',
  },
  description: {
    fontSize: '16px',
    color: '#666',
    marginBottom: '15px',
  },
  button: {
    padding: '10px 20px',
    background: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    cursor: 'pointer',
  },
}
