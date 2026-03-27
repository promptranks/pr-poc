/**
 * Leaderboard page: public rankings with Matrix green theme.
 * Fetches GET /leaderboard with optional auth for personal rank highlighting.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const PERIODS = [
  { value: 'alltime', label: 'All Time' },
  { value: 'weekly', label: 'This Week' },
  { value: 'monthly', label: 'This Month' },
  { value: 'quarterly', label: 'This Quarter' },
]

const LEVEL_LABELS: Record<number, string> = {
  1: 'NOVICE',
  2: 'PRACTITIONER',
  3: 'PROFICIENT',
  4: 'EXPERT',
  5: 'MASTER',
}

const LEVEL_COLORS: Record<number, string> = {
  1: '#666666',
  2: '#008f11',
  3: '#00ff41',
  4: '#6D5FFA',
  5: '#EC41FB',
}

const RANK_COLORS: Record<number, string> = {
  1: '#FFD700',
  2: '#C0C0C0',
  3: '#CD7F32',
}

interface LeaderboardEntry {
  rank: number
  user_id: string
  display_name: string
  level: number
  level_name: string
  score: number
  pillar_scores: Record<string, number | Record<string, number>>
  badge_id: string
  achieved_at: string
}

interface MyRank {
  rank: number
  score: number
}

interface LeaderboardResponse {
  entries: LeaderboardEntry[]
  total: number
  page: number
  page_size: number
  period: string
  my_rank: MyRank | null
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
  },
  container: {
    maxWidth: 900,
    width: '100%',
    padding: '3rem 2rem',
  },
  heading: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '1.4rem',
    color: '#00ff41',
    textAlign: 'center' as const,
    marginBottom: '0.5rem',
    textShadow: '0 0 20px rgba(0,255,65,0.5)',
    letterSpacing: '4px',
  },
  subtitle: {
    fontSize: '0.85rem',
    color: '#008f11',
    textAlign: 'center' as const,
    marginBottom: '2rem',
  },
  tabRow: {
    display: 'flex',
    gap: '0.5rem',
    justifyContent: 'center',
    flexWrap: 'wrap' as const,
    marginBottom: '1.5rem',
  },
  tab: (active: boolean) => ({
    padding: '8px 16px',
    border: active ? '1px solid #00ff41' : '1px solid rgba(0,255,65,0.2)',
    borderRadius: 4,
    background: active ? 'rgba(0,255,65,0.1)' : 'rgba(0,15,0,0.4)',
    color: active ? '#00ff41' : '#008f11',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '0.8rem',
    cursor: 'pointer',
    transition: 'all 0.15s',
  }),
  myRankCard: {
    padding: '1rem 1.5rem',
    border: '1px solid #FFD700',
    borderRadius: 8,
    background: 'rgba(255,215,0,0.05)',
    marginBottom: '1.5rem',
    display: 'flex',
    alignItems: 'center',
    gap: '1.5rem',
    flexWrap: 'wrap' as const,
  },
  myRankLabel: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.55rem',
    color: '#FFD700',
    letterSpacing: '2px',
  },
  myRankValue: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '1.2rem',
    color: '#FFD700',
    textShadow: '0 0 10px rgba(255,215,0,0.4)',
  },
  ctaBanner: {
    padding: '1rem 1.5rem',
    border: '1px solid rgba(0,255,65,0.15)',
    borderRadius: 8,
    background: 'rgba(0,15,0,0.5)',
    marginBottom: '1.5rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap' as const,
    gap: '1rem',
  },
  ctaText: {
    fontSize: '0.85rem',
    color: '#008f11',
  },
  ctaButton: {
    padding: '10px 20px',
    borderRadius: 4,
    border: 'none',
    background: 'linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 40%, #EC41FB 100%)',
    color: '#fff',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '0.8rem',
    cursor: 'pointer',
    whiteSpace: 'nowrap' as const,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    marginBottom: '1.5rem',
  },
  th: {
    padding: '10px 12px',
    borderBottom: '1px solid rgba(0,255,65,0.2)',
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.45rem',
    color: '#008f11',
    textAlign: 'left' as const,
    letterSpacing: '1px',
    textTransform: 'uppercase' as const,
  },
  tr: (isCurrentUser: boolean, rank: number) => ({
    borderBottom: '1px solid rgba(0,255,65,0.08)',
    background: isCurrentUser
      ? 'rgba(255,215,0,0.05)'
      : rank <= 3
      ? 'rgba(0,255,65,0.03)'
      : 'transparent',
    outline: isCurrentUser ? '1px solid rgba(255,215,0,0.3)' : 'none',
    transition: 'background 0.1s',
  }),
  td: {
    padding: '10px 12px',
    fontSize: '0.85rem',
    color: '#c0ffc0',
    verticalAlign: 'middle' as const,
  },
  rankCell: (rank: number) => ({
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.7rem',
    color: RANK_COLORS[rank] || '#008f11',
    textShadow: rank <= 3 ? `0 0 8px ${RANK_COLORS[rank]}60` : 'none',
    minWidth: 36,
  }),
  levelBadge: (level: number) => ({
    display: 'inline-block',
    padding: '3px 8px',
    borderRadius: 3,
    border: `1px solid ${LEVEL_COLORS[level] || '#008f11'}`,
    color: LEVEL_COLORS[level] || '#008f11',
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.4rem',
    letterSpacing: '1px',
    background: `${LEVEL_COLORS[level] || '#008f11'}15`,
  }),
  scoreBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  barBg: {
    flex: 1,
    height: 6,
    background: 'rgba(0,255,65,0.1)',
    borderRadius: 3,
    overflow: 'hidden' as const,
    minWidth: 60,
  },
  barFill: (score: number) => ({
    height: '100%',
    width: `${score}%`,
    background: score >= 85
      ? 'linear-gradient(90deg, #6D5FFA, #EC41FB)'
      : score >= 70
      ? '#00ff41'
      : '#008f11',
    borderRadius: 3,
  }),
  scoreNum: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.65rem',
    color: '#00ff41',
    minWidth: 28,
    textAlign: 'right' as const,
  },
  pecamMini: {
    display: 'flex',
    gap: 3,
    alignItems: 'flex-end',
  },
  pecamBar: (val: number) => ({
    width: 6,
    height: Math.max(4, Math.round((val / 100) * 20)),
    background: `rgba(0,255,65,${0.3 + (val / 100) * 0.7})`,
    borderRadius: '2px 2px 0 0',
  }),
  pagination: {
    display: 'flex',
    gap: '0.5rem',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: '1rem',
  },
  pageBtn: (active: boolean) => ({
    padding: '6px 12px',
    border: active ? '1px solid #00ff41' : '1px solid rgba(0,255,65,0.2)',
    borderRadius: 3,
    background: active ? 'rgba(0,255,65,0.1)' : 'transparent',
    color: active ? '#00ff41' : '#008f11',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '0.8rem',
    cursor: 'pointer',
  }),
  loading: {
    textAlign: 'center' as const,
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.7rem',
    color: '#00ff41',
    padding: '4rem',
    letterSpacing: '2px',
  },
  error: {
    textAlign: 'center' as const,
    color: '#ff4444',
    fontSize: '0.85rem',
    padding: '2rem',
  },
  empty: {
    textAlign: 'center' as const,
    color: '#008f11',
    fontSize: '0.85rem',
    padding: '3rem',
    fontFamily: "'Press Start 2P', monospace",
    fontSize2: '0.6rem',
  },
  footer: {
    marginTop: '2rem',
    paddingTop: '1.5rem',
    borderTop: '1px solid rgba(0,255,65,0.1)',
    fontSize: '0.75rem',
    color: '#008f11',
    textAlign: 'center' as const,
  },
  backLink: {
    display: 'inline-block',
    marginBottom: '1.5rem',
    color: '#008f11',
    fontSize: '0.8rem',
    cursor: 'pointer',
    textDecoration: 'none',
  },
}

function getPillarCombined(pillarScores: Record<string, number | Record<string, number>>): number[] {
  const pillars = ['P', 'E', 'C', 'A', 'M']
  return pillars.map((p) => {
    const v = pillarScores[p]
    if (typeof v === 'number') return v
    if (v && typeof v === 'object') return (v as Record<string, number>).combined ?? 0
    return 0
  })
}

export default function Leaderboard() {
  const navigate = useNavigate()
  const [period, setPeriod] = useState('alltime')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<LeaderboardResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const token = sessionStorage.getItem('auth_token')

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError('')
      try {
        const headers: Record<string, string> = {}
        if (token) headers['Authorization'] = `Bearer ${token}`

        const res = await fetch(
          `${API_BASE}/leaderboard/?period=${period}&page=${page}&page_size=50`,
          { headers },
        )
        if (!res.ok) {
          const d = await res.json().catch(() => ({}))
          throw new Error(d.detail || `HTTP ${res.status}`)
        }
        const json: LeaderboardResponse = await res.json()
        setData(json)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load leaderboard')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [period, page, token])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 50)) : 1

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <div
          style={styles.backLink}
          onClick={() => navigate('/')}
          role="link"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/')}
        >
          &lt; Back
        </div>

        <h1 style={styles.heading}>LEADERBOARD</h1>
        <p style={styles.subtitle}>Top prompt engineers ranked by Full Assessment score</p>

        {/* Period tabs */}
        <div style={styles.tabRow}>
          {PERIODS.map((p) => (
            <button
              key={p.value}
              style={styles.tab(period === p.value)}
              onClick={() => { setPeriod(p.value); setPage(1) }}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* My rank card */}
        {data?.my_rank && (
          <div style={styles.myRankCard}>
            <div>
              <div style={styles.myRankLabel}>YOUR RANK</div>
              <div style={styles.myRankValue}>#{data.my_rank.rank}</div>
            </div>
            <div>
              <div style={styles.myRankLabel}>YOUR SCORE</div>
              <div style={styles.myRankValue}>{data.my_rank.score}</div>
            </div>
          </div>
        )}

        {/* CTA for unranked users */}
        {data && !data.my_rank && !token && (
          <div style={styles.ctaBanner}>
            <span style={styles.ctaText}>Take the Full Assessment to appear on the leaderboard</span>
            <button style={styles.ctaButton} onClick={() => navigate('/')}>
              Start Assessment
            </button>
          </div>
        )}

        {loading && (
          <div style={styles.loading}>[ LOADING... ]</div>
        )}

        {error && !loading && (
          <div style={styles.error}>{error}</div>
        )}

        {!loading && !error && data && data.entries.length === 0 && (
          <div style={{ ...styles.empty, fontSize: '0.6rem' }}>
            No entries yet. Be the first to complete a Full Assessment.
          </div>
        )}

        {!loading && !error && data && data.entries.length > 0 && (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>#</th>
                <th style={styles.th}>Name</th>
                <th style={styles.th}>Level</th>
                <th style={styles.th}>Score</th>
                <th style={styles.th}>PECAM</th>
                <th style={{ ...styles.th, display: 'none' as const }}>Date</th>
              </tr>
            </thead>
            <tbody>
              {data.entries.map((entry) => {
                const isMe = token
                  ? data.my_rank?.rank === entry.rank
                  : false
                const pillarVals = getPillarCombined(entry.pillar_scores)
                const rankColor = RANK_COLORS[entry.rank]

                return (
                  <tr
                    key={entry.user_id}
                    style={styles.tr(isMe, entry.rank)}
                  >
                    <td style={{ ...styles.td, ...styles.rankCell(entry.rank) }}>
                      {entry.rank <= 3 ? ['', '01', '02', '03'][entry.rank] : entry.rank}
                    </td>
                    <td style={styles.td}>
                      <span style={{ color: isMe ? '#FFD700' : rankColor || '#c0ffc0' }}>
                        {entry.display_name}
                        {isMe && ' (you)'}
                      </span>
                    </td>
                    <td style={styles.td}>
                      <span style={styles.levelBadge(entry.level)}>
                        L{entry.level} {LEVEL_LABELS[entry.level] || ''}
                      </span>
                    </td>
                    <td style={styles.td}>
                      <div style={styles.scoreBar}>
                        <div style={styles.barBg}>
                          <div style={styles.barFill(entry.score)} />
                        </div>
                        <span style={styles.scoreNum}>{Math.round(entry.score)}</span>
                      </div>
                    </td>
                    <td style={styles.td}>
                      <div style={styles.pecamMini}>
                        {pillarVals.map((v, i) => (
                          <div key={i} style={styles.pecamBar(v)} title={`${['P','E','C','A','M'][i]}: ${Math.round(v)}`} />
                        ))}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={styles.pagination}>
            <button
              style={styles.pageBtn(false)}
              disabled={page === 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              &lt; Prev
            </button>
            {Array.from({ length: Math.min(7, totalPages) }, (_, i) => {
              const p = i + 1
              return (
                <button
                  key={p}
                  style={styles.pageBtn(p === page)}
                  onClick={() => setPage(p)}
                >
                  {p}
                </button>
              )
            })}
            <button
              style={styles.pageBtn(false)}
              disabled={page === totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next &gt;
            </button>
          </div>
        )}

        <div style={styles.footer}>
          Full Assessment scores only &mdash; PromptRanks PECAM Framework
        </div>
      </div>
    </div>
  )
}
