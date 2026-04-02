import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate, useSearchParams } from 'react-router-dom'
import AssessmentHistoryTable from '../components/AssessmentHistoryTable'
import AnalyticsCharts from '../components/AnalyticsCharts'
import Recommendations from '../components/Recommendations'
import SubscriptionCard from '../components/SubscriptionCard'
import UpgradeModal from '../components/UpgradeModal'

interface DashboardData {
  user: {
    id: string
    email: string
    name: string
    avatar_url?: string
    subscription_tier: string
  }
  usage: {
    full_assessments_used: number
    full_assessments_limit: number
    tier: string
  }
  recent_assessments: any[]
}

interface AnalyticsData {
  scoreTrend: any[]
  pillarComparison: any
  skillGaps: string[]
  recommendations: any[]
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Dashboard() {
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [data, setData] = useState<DashboardData | null>(null)
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [refreshMessage, setRefreshMessage] = useState('')

  useEffect(() => {
    void fetchDashboard()
    void fetchAnalytics()
    void claimPendingBadges()
  }, [token])

  const claimPendingBadges = async () => {
    if (!token) return

    try {
      // Fetch unclaimed badges
      const res = await fetch(`${API_URL}/dashboard/unclaimed-badges`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (!res.ok) return

      const data = await res.json()
      const unclaimedBadges = data.unclaimed_badges || []

      // Auto-claim all unclaimed badges
      for (const badge of unclaimedBadges) {
        try {
          const res = await fetch(`${API_URL}/assessments/${badge.assessment_id}/claim`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({}),
          })
          // 409 means already claimed, which is fine - just ignore it
          if (!res.ok && res.status !== 409) {
            console.error('Failed to claim badge:', res.status)
          }
        } catch (err) {
          console.error('Failed to claim badge:', err)
        }
      }

      // Refresh dashboard if we claimed any badges
      if (unclaimedBadges.length > 0) {
        await fetchDashboard()
      }
    } catch (error) {
      console.error('Failed to claim pending badges:', error)
    }
  }

  useEffect(() => {
    if (!token) return

    const sessionId = searchParams.get('session_id')
    if (!sessionId) return

    let cancelled = false

    const refreshAfterCheckout = async () => {
      setRefreshMessage('Finalizing your premium upgrade...')

      // First, try to sync subscription from Stripe
      try {
        const syncRes = await fetch(`${API_URL}/payments/sync-subscription`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ session_id: sessionId }),
        })

        if (syncRes.ok) {
          const syncData = await syncRes.json()
          if (syncData.subscription_tier === 'premium') {
            // Successfully synced, refresh dashboard
            await fetchDashboard({ keepLoading: false })
            sessionStorage.setItem('pending_subscription_upgrade', 'completed')
            setRefreshMessage('')
            const nextParams = new URLSearchParams(searchParams)
            nextParams.delete('session_id')
            setSearchParams(nextParams, { replace: true })
            return
          }
        }
      } catch (err) {
        console.error('Sync failed, falling back to polling:', err)
      }

      // Fallback: poll dashboard endpoint
      for (let attempt = 0; attempt < 6; attempt += 1) {
        const dashboardData = await fetchDashboard({ keepLoading: attempt === 0 })

        if (cancelled) return

        if (dashboardData?.user.subscription_tier && dashboardData.user.subscription_tier !== 'free') {
          sessionStorage.setItem('pending_subscription_upgrade', 'completed')
          setRefreshMessage('')
          const nextParams = new URLSearchParams(searchParams)
          nextParams.delete('session_id')
          setSearchParams(nextParams, { replace: true })
          return
        }

        await new Promise((resolve) => setTimeout(resolve, 1500))
      }

      if (cancelled) return
      setRefreshMessage('Payment succeeded. Subscription sync is still in progress — refresh again in a moment if needed.')
    }

    void refreshAfterCheckout()

    return () => {
      cancelled = true
    }
  }, [searchParams, setSearchParams, token])

  const fetchDashboard = async ({ keepLoading = true }: { keepLoading?: boolean } = {}) => {
    if (!token) return null

    if (keepLoading) {
      setLoading(true)
    }

    try {
      const response = await fetch(`${API_URL}/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (response.ok) {
        const result = await response.json()
        setData(result)
        return result
      }
    } catch (error) {
      console.error('Failed to fetch dashboard:', error)
    } finally {
      if (keepLoading) {
        setLoading(false)
      }
    }

    return null
  }

  const fetchAnalytics = async () => {
    if (!token) return

    try {
      const [trendRes, compRes, gapsRes, recsRes] = await Promise.all([
        fetch(`${API_URL}/analytics/score-trend`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/analytics/pillar-comparison`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/analytics/skill-gaps`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/analytics/recommendations`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ])

      if (trendRes.ok && compRes.ok && gapsRes.ok && recsRes.ok) {
        setAnalytics({
          scoreTrend: await trendRes.json(),
          pillarComparison: await compRes.json(),
          skillGaps: await gapsRes.json(),
          recommendations: await recsRes.json()
        })
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
    }
  }

  if (loading) return (
    <div style={styles.container}>
      <div style={styles.loadingContainer}>
        <div style={styles.spinner}></div>
        <p style={styles.loadingText}>Loading dashboard...</p>
      </div>
    </div>
  )

  if (!data) return (
    <div style={styles.container}>
      <div style={styles.errorContainer}>
        <p style={styles.errorText}>Failed to load dashboard</p>
        <button onClick={() => void fetchDashboard()} style={styles.retryButton}>Retry</button>
      </div>
    </div>
  )

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>Dashboard</h1>
          <p style={styles.subtitle}>{data.user.email}</p>
        </div>
        <div style={styles.headerActions}>
          <span style={styles.tierBadge}>{data.user.subscription_tier}</span>
          <button onClick={() => navigate('/')} style={styles.button}>Home</button>
          <button onClick={logout} style={styles.logoutButton}>Logout</button>
        </div>
      </header>

      {refreshMessage && (
        <div style={styles.syncBanner}>
          {refreshMessage}
        </div>
      )}

      <div style={styles.ctaCard}>
        <div>
          <h2 style={styles.ctaTitle}>Start your next assessment</h2>
          <p style={styles.ctaText}>
            Launch a quick check-in or a full assessment from the main assessment page.
          </p>
        </div>
        <div style={styles.ctaActions}>
          <button style={styles.primaryCtaButton} onClick={() => navigate('/')}>
            Start Assessment
          </button>
          <button style={styles.secondaryCtaButton} onClick={() => navigate('/?mode=full')}>
            Full Assessment
          </button>
        </div>
      </div>

      {data.usage.tier === 'premium' && (
        <div style={styles.usageCard}>
          <h3>Usage This Month</h3>
          <p style={styles.usageText}>
            {data.usage.full_assessments_used} / {data.usage.full_assessments_limit} full assessments used
          </p>
          <div style={styles.progressBar}>
            <div
              style={{
                ...styles.progressFill,
                width: `${(data.usage.full_assessments_used / data.usage.full_assessments_limit) * 100}%`
              }}
            />
          </div>
        </div>
      )}

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Recent Assessments</h2>
        <AssessmentHistoryTable assessments={data.recent_assessments} />
      </div>

      {(data.user.subscription_tier === 'premium' || data.user.subscription_tier === 'enterprise') && analytics && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Analytics</h2>
          <AnalyticsCharts
            scoreTrend={analytics.scoreTrend}
            pillarComparison={analytics.pillarComparison}
          />
          <Recommendations
            recommendations={analytics.recommendations}
            weakPillars={analytics.skillGaps}
          />
        </div>
      )}

      {data.user.subscription_tier === 'free' && (
        <div style={styles.upgradePrompt}>
          <h3>Unlock Analytics & Recommendations</h3>
          <p>Upgrade to Premium to see score trends, pillar comparisons, and personalized learning recommendations.</p>
          <button style={styles.upgradeButton} onClick={() => setShowUpgradeModal(true)}>Upgrade to Premium</button>
        </div>
      )}

      <SubscriptionCard
        tier={data.user.subscription_tier}
        plan={sessionStorage.getItem('pending_subscription_plan') || undefined}
      />

      <UpgradeModal isOpen={showUpgradeModal} onClose={() => setShowUpgradeModal(false)} />
    </div>
  )
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#0a0a0a',
    color: '#00ff41',
    padding: '2rem',
    fontFamily: "'Courier New', monospace",
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
    paddingBottom: '1rem',
    borderBottom: '1px solid #00ff41',
  },
  title: {
    fontSize: '2rem',
    margin: '0 0 0.5rem 0',
    fontWeight: 'bold' as const,
  },
  subtitle: {
    color: '#008f11',
    margin: 0,
    fontSize: '0.9rem',
  },
  headerActions: {
    display: 'flex',
    gap: '0.75rem',
    alignItems: 'center',
  },
  tierBadge: {
    padding: '0.5rem 1rem',
    background: 'transparent',
    color: '#00ff41',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    fontSize: '0.8rem',
    textTransform: 'uppercase' as const,
    fontFamily: "'Courier New', monospace",
  },
  button: {
    padding: '0.5rem 1rem',
    background: 'transparent',
    color: '#00ff41',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    cursor: 'pointer',
    fontFamily: "'Courier New', monospace",
    fontSize: '0.9rem',
  },
  logoutButton: {
    padding: '0.5rem 1rem',
    background: 'transparent',
    color: '#ff4444',
    border: '1px solid #ff4444',
    borderRadius: '4px',
    cursor: 'pointer',
    fontFamily: "'Courier New', monospace",
    fontSize: '0.9rem',
  },
  syncBanner: {
    marginBottom: '1.5rem',
    padding: '1rem',
    borderRadius: '4px',
    background: '#1a1a1a',
    color: '#00ff41',
    border: '1px solid #00ff41',
    fontFamily: "'Courier New', monospace",
  },
  ctaCard: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '1rem',
    padding: '1.5rem',
    marginBottom: '2rem',
    borderRadius: '4px',
    background: '#1a1a1a',
    border: '1px solid #00ff41',
    flexWrap: 'wrap' as const,
  },
  ctaTitle: {
    fontSize: '1.5rem',
    margin: '0 0 0.5rem 0',
    fontWeight: 'bold' as const,
  },
  ctaText: {
    margin: 0,
    color: '#008f11',
    lineHeight: 1.6,
    fontSize: '0.9rem',
  },
  ctaActions: {
    display: 'flex',
    gap: '0.75rem',
    flexWrap: 'wrap' as const,
  },
  primaryCtaButton: {
    padding: '0.75rem 1.5rem',
    background: 'transparent',
    color: '#00ff41',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold' as const,
    fontFamily: "'Courier New', monospace",
  },
  secondaryCtaButton: {
    padding: '0.75rem 1.5rem',
    background: '#00ff41',
    color: '#0a0a0a',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold' as const,
    fontFamily: "'Courier New', monospace",
  },
  usageCard: {
    background: '#1a1a1a',
    padding: '1.5rem',
    borderRadius: '4px',
    border: '1px solid #00ff41',
    marginBottom: '2rem',
  },
  usageText: {
    fontSize: '1.1rem',
    margin: '0.75rem 0',
    color: '#00ff41',
  },
  progressBar: {
    width: '100%',
    height: '1.25rem',
    background: '#0a0a0a',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: '#00ff41',
    transition: 'width 0.3s ease',
  },
  section: {
    marginTop: '2rem',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    marginBottom: '1rem',
    fontWeight: 'bold' as const,
  },
  upgradePrompt: {
    marginTop: '2rem',
    padding: '2rem',
    background: '#1a1a1a',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    textAlign: 'center' as const,
  },
  upgradeButton: {
    marginTop: '1rem',
    padding: '0.75rem 1.5rem',
    background: 'transparent',
    color: '#00ff41',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
    fontFamily: "'Courier New', monospace",
    fontWeight: 'bold' as const,
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    backgroundColor: '#0a0a0a',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '4px solid #1a1a1a',
    borderTop: '4px solid #00ff41',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  loadingText: {
    marginTop: '1.5rem',
    color: '#008f11',
    fontFamily: "'Courier New', monospace",
  },
  errorContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    backgroundColor: '#0a0a0a',
  },
  errorText: {
    color: '#ff4444',
    fontSize: '1.1rem',
    marginBottom: '1.5rem',
    fontFamily: "'Courier New', monospace",
  },
  retryButton: {
    padding: '0.75rem 1.5rem',
    background: 'transparent',
    color: '#00ff41',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    cursor: 'pointer',
    fontFamily: "'Courier New', monospace",
  },
}
