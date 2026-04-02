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
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '20px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '30px',
    paddingBottom: '20px',
    borderBottom: '1px solid #ddd',
  },
  title: {
    fontSize: '32px',
    margin: '0 0 5px 0',
  },
  subtitle: {
    color: '#666',
    margin: 0,
  },
  headerActions: {
    display: 'flex',
    gap: '10px',
    alignItems: 'center',
  },
  tierBadge: {
    padding: '6px 12px',
    background: '#007bff',
    color: 'white',
    borderRadius: '4px',
    fontSize: '14px',
    textTransform: 'uppercase' as const,
  },
  button: {
    padding: '8px 16px',
    background: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  logoutButton: {
    padding: '8px 16px',
    background: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  syncBanner: {
    marginBottom: '20px',
    padding: '14px 16px',
    borderRadius: '8px',
    background: '#fff4ce',
    color: '#7a4b00',
    border: '1px solid #f3d98b',
  },
  ctaCard: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '16px',
    padding: '24px',
    marginBottom: '30px',
    borderRadius: '12px',
    background: '#f8f9fa',
    border: '1px solid #e5e7eb',
    flexWrap: 'wrap' as const,
  },
  ctaTitle: {
    fontSize: '24px',
    margin: '0 0 8px 0',
  },
  ctaText: {
    margin: 0,
    color: '#4b5563',
    lineHeight: 1.6,
  },
  ctaActions: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap' as const,
  },
  primaryCtaButton: {
    padding: '12px 20px',
    background: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 700,
  },
  secondaryCtaButton: {
    padding: '12px 20px',
    background: 'white',
    color: '#007bff',
    border: '1px solid #007bff',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 700,
  },
  usageCard: {
    background: '#f8f9fa',
    padding: '20px',
    borderRadius: '8px',
    marginBottom: '30px',
  },
  usageText: {
    fontSize: '18px',
    margin: '10px 0',
  },
  progressBar: {
    width: '100%',
    height: '20px',
    background: '#e9ecef',
    borderRadius: '10px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: '#28a745',
    transition: 'width 0.3s ease',
  },
  section: {
    marginTop: '30px',
  },
  sectionTitle: {
    fontSize: '24px',
    marginBottom: '10px',
  },
  upgradePrompt: {
    marginTop: '30px',
    padding: '30px',
    background: '#e7f3ff',
    borderRadius: '8px',
    textAlign: 'center' as const,
  },
  upgradeButton: {
    marginTop: '15px',
    padding: '12px 24px',
    background: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    cursor: 'pointer',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '400px',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '4px solid #f3f3f3',
    borderTop: '4px solid #007bff',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  loadingText: {
    marginTop: '20px',
    color: '#666',
  },
  errorContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '400px',
  },
  errorText: {
    color: '#dc3545',
    fontSize: '18px',
    marginBottom: '20px',
  },
  retryButton: {
    padding: '10px 20px',
    background: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
}
