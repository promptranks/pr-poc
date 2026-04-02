import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'

interface ScoreTrend {
  date: string
  score: number
  mode: string
}

interface PillarComparison {
  latest: Record<string, number>
  average: Record<string, number>
}

interface AnalyticsChartsProps {
  scoreTrend: ScoreTrend[]
  pillarComparison: PillarComparison
}

export default function AnalyticsCharts({ scoreTrend, pillarComparison }: AnalyticsChartsProps) {
  const radarData = Object.keys(pillarComparison.latest).map(pillar => ({
    pillar,
    latest: pillarComparison.latest[pillar] || 0,
    average: pillarComparison.average[pillar] || 0
  }))

  const lineData = scoreTrend.map(item => ({
    date: new Date(item.date).toLocaleDateString(),
    score: item.score
  }))

  if (scoreTrend.length < 2) {
    return (
      <div style={styles.notice}>
        Complete at least 2 assessments to see your score trends.
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.chartSection}>
        <h3 style={styles.chartTitle}>Score Trend</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={lineData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
            <XAxis dataKey="date" stroke="#00ff41" />
            <YAxis domain={[0, 100]} stroke="#00ff41" />
            <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #00ff41', color: '#00ff41' }} />
            <Legend />
            <Line type="monotone" dataKey="score" stroke="#00ff41" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={styles.chartSection}>
        <h3 style={styles.chartTitle}>Pillar Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#1a1a1a" />
            <PolarAngleAxis dataKey="pillar" stroke="#00ff41" />
            <PolarRadiusAxis domain={[0, 100]} stroke="#00ff41" />
            <Radar name="Latest" dataKey="latest" stroke="#00ff41" fill="#00ff41" fillOpacity={0.3} />
            <Radar name="Average" dataKey="average" stroke="#008f11" fill="#008f11" fillOpacity={0.2} />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

const styles = {
  container: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1.5rem',
    marginTop: '1.5rem',
  },
  chartSection: {
    background: '#1a1a1a',
    padding: '1.5rem',
    borderRadius: '4px',
    border: '1px solid #00ff41',
  },
  chartTitle: {
    fontSize: '1.2rem',
    marginBottom: '1rem',
    color: '#00ff41',
    fontFamily: "'Courier New', monospace",
    fontWeight: 'bold' as const,
  },
  notice: {
    padding: '1.5rem',
    background: '#1a1a1a',
    borderRadius: '4px',
    border: '1px solid #00ff41',
    color: '#008f11',
    textAlign: 'center' as const,
    fontFamily: "'Courier New', monospace",
  },
}
