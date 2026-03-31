import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface UsageData {
  can_start_full: boolean
  full_assessments_used: number
  full_assessments_limit: number
  tier: string
}

export default function UsageBadge() {
  const { user, token } = useAuth()
  const [usage, setUsage] = useState<UsageData | null>(null)

  useEffect(() => {
    if (!user || !token) return

    const fetchUsage = async () => {
      try {
        const res = await fetch(`${API_URL}/usage/check`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) {
          const data = await res.json()
          setUsage(data)
        }
      } catch (err) {
        // Silently fail
      }
    }
    fetchUsage()
  }, [user, token])

  if (!usage || usage.tier !== 'premium') return null

  return (
    <div style={styles.badge}>
      {usage.full_assessments_used}/{usage.full_assessments_limit} assessments
    </div>
  )
}

const styles = {
  badge: {
    padding: '6px 12px',
    borderRadius: '4px',
    background: 'rgba(0,255,65,0.1)',
    border: '1px solid rgba(0,255,65,0.3)',
    color: '#00ff41',
    fontSize: '0.75rem',
    fontFamily: "'Share Tech Mono', monospace",
  }
}
