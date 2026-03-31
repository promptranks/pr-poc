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
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="score" stroke="#007bff" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={styles.chartSection}>
        <h3 style={styles.chartTitle}>Pillar Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="pillar" />
            <PolarRadiusAxis domain={[0, 100]} />
            <Radar name="Latest" dataKey="latest" stroke="#007bff" fill="#007bff" fillOpacity={0.6} />
            <Radar name="Average" dataKey="average" stroke="#28a745" fill="#28a745" fillOpacity={0.3} />
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
    gap: '20px',
    marginTop: '20px',
  },
  chartSection: {
    background: '#f8f9fa',
    padding: '20px',
    borderRadius: '8px',
  },
  chartTitle: {
    fontSize: '18px',
    marginBottom: '15px',
  },
  notice: {
    padding: '20px',
    background: '#fff3cd',
    borderRadius: '8px',
    color: '#856404',
    textAlign: 'center' as const,
  },
}
