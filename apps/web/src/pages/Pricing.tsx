import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Pricing() {
  const navigate = useNavigate()
  const { token } = useAuth()

  const handleUpgrade = async (plan: string) => {
    if (!token) {
      navigate('/auth')
      return
    }

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/payments/create-checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ plan })
      })

      if (response.ok) {
        const { checkout_url } = await response.json()
        window.location.href = checkout_url
      }
    } catch (error) {
      console.error('Failed to create checkout:', error)
    }
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Choose Your Plan</h1>
      <p style={styles.subtitle}>Unlock your full potential with PromptRanks</p>

      <div style={styles.plans}>
        <div style={styles.plan}>
          <h3 style={styles.planName}>Free</h3>
          <div style={styles.price}>$0</div>
          <ul style={styles.features}>
            <li>Unlimited quick assessments</li>
            <li>Basic badge</li>
            <li>Leaderboard access</li>
          </ul>
          <button style={styles.buttonDisabled} disabled>Current Plan</button>
        </div>

        <div style={{ ...styles.plan, ...styles.planHighlight }}>
          <h3 style={styles.planName}>Premium</h3>
          <div style={styles.price}>$19<span style={styles.period}>/month</span></div>
          <ul style={styles.features}>
            <li>3 full assessments/month</li>
            <li>Industry & role targeting</li>
            <li>Advanced analytics</li>
            <li>Priority support</li>
          </ul>
          <button style={styles.button} onClick={() => handleUpgrade('premium_monthly')}>
            Upgrade to Premium
          </button>
        </div>

        <div style={styles.plan}>
          <h3 style={styles.planName}>Enterprise</h3>
          <div style={styles.price}>Custom</div>
          <ul style={styles.features}>
            <li>Unlimited assessments</li>
            <li>Team management</li>
            <li>API access</li>
            <li>Dedicated support</li>
          </ul>
          <button style={styles.buttonSecondary} onClick={() => navigate('/contact')}>
            Contact Sales
          </button>
        </div>
      </div>
    </div>
  )
}

const styles = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '40px 20px',
    textAlign: 'center' as const,
  },
  title: {
    fontSize: '36px',
    marginBottom: '10px',
  },
  subtitle: {
    fontSize: '18px',
    color: '#666',
    marginBottom: '40px',
  },
  plans: {
    display: 'flex',
    gap: '20px',
    justifyContent: 'center',
    flexWrap: 'wrap' as const,
  },
  plan: {
    background: 'white',
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '30px',
    width: '300px',
  },
  planHighlight: {
    border: '2px solid #007bff',
    transform: 'scale(1.05)',
  },
  planName: {
    fontSize: '24px',
    marginBottom: '10px',
  },
  price: {
    fontSize: '48px',
    fontWeight: 'bold' as const,
    marginBottom: '20px',
  },
  period: {
    fontSize: '18px',
    color: '#666',
  },
  features: {
    listStyle: 'none',
    padding: 0,
    marginBottom: '30px',
    textAlign: 'left' as const,
  },
  button: {
    width: '100%',
    padding: '12px',
    background: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    cursor: 'pointer',
  },
  buttonSecondary: {
    width: '100%',
    padding: '12px',
    background: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    cursor: 'pointer',
  },
  buttonDisabled: {
    width: '100%',
    padding: '12px',
    background: '#e9ecef',
    color: '#6c757d',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    cursor: 'not-allowed',
  },
}
