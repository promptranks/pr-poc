interface Resource {
  id: string
  title: string
  url: string
  pillar: string
  resource_type: string
}

interface RecommendationsProps {
  recommendations: Resource[]
  weakPillars: string[]
}

const pillarNames: Record<string, string> = {
  P: 'Precision',
  E: 'Efficiency',
  C: 'Clarity',
  A: 'Adaptability',
  M: 'Mastery'
}

export default function Recommendations({ recommendations, weakPillars }: RecommendationsProps) {
  if (recommendations.length === 0) {
    return (
      <div style={styles.empty}>
        Complete an assessment to get personalized recommendations.
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>Recommended Focus Areas</h3>
        <p style={styles.subtitle}>
          Based on your latest assessment, focus on: {weakPillars.map(p => pillarNames[p]).join(', ')}
        </p>
      </div>

      <div style={styles.resourceGrid}>
        {recommendations.map(resource => (
          <a
            key={resource.id}
            href={resource.url}
            target="_blank"
            rel="noopener noreferrer"
            style={styles.resourceCard}
          >
            <div style={styles.resourceHeader}>
              <span style={styles.pillarBadge}>{pillarNames[resource.pillar]}</span>
              <span style={styles.typeBadge}>{resource.resource_type}</span>
            </div>
            <h4 style={styles.resourceTitle}>{resource.title}</h4>
          </a>
        ))}
      </div>

      <div style={styles.cta}>
        <p>Take another assessment to track your improvement</p>
      </div>
    </div>
  )
}

const styles = {
  container: {
    marginTop: '1.5rem',
  },
  header: {
    marginBottom: '1.5rem',
  },
  title: {
    fontSize: '1.2rem',
    marginBottom: '0.5rem',
    color: '#00ff41',
    fontFamily: "'Courier New', monospace",
    fontWeight: 'bold' as const,
  },
  subtitle: {
    color: '#008f11',
    fontSize: '0.9rem',
    fontFamily: "'Courier New', monospace",
  },
  resourceGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
    gap: '1rem',
  },
  resourceCard: {
    background: '#1a1a1a',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    padding: '1rem',
    textDecoration: 'none',
    color: '#00ff41',
    transition: 'transform 0.2s, box-shadow 0.2s',
    cursor: 'pointer',
    fontFamily: "'Courier New', monospace",
  },
  resourceHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '0.75rem',
  },
  pillarBadge: {
    padding: '0.25rem 0.5rem',
    background: 'transparent',
    color: '#00ff41',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    fontSize: '0.75rem',
  },
  typeBadge: {
    padding: '0.25rem 0.5rem',
    background: 'transparent',
    color: '#008f11',
    border: '1px solid #008f11',
    borderRadius: '4px',
    fontSize: '0.75rem',
  },
  resourceTitle: {
    fontSize: '1rem',
    margin: 0,
    color: '#00ff41',
  },
  cta: {
    marginTop: '1.5rem',
    padding: '1rem',
    background: '#1a1a1a',
    border: '1px solid #00ff41',
    borderRadius: '4px',
    textAlign: 'center' as const,
    color: '#008f11',
    fontFamily: "'Courier New', monospace",
  },
  empty: {
    padding: '1.5rem',
    textAlign: 'center' as const,
    color: '#008f11',
    fontFamily: "'Courier New', monospace",
  },
}
