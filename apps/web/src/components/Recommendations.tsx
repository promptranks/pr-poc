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
    marginTop: '20px',
  },
  header: {
    marginBottom: '20px',
  },
  title: {
    fontSize: '20px',
    marginBottom: '8px',
  },
  subtitle: {
    color: '#666',
    fontSize: '14px',
  },
  resourceGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
    gap: '15px',
  },
  resourceCard: {
    background: '#fff',
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '15px',
    textDecoration: 'none',
    color: 'inherit',
    transition: 'transform 0.2s, box-shadow 0.2s',
    cursor: 'pointer',
  },
  resourceHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '10px',
  },
  pillarBadge: {
    padding: '4px 8px',
    background: '#007bff',
    color: 'white',
    borderRadius: '4px',
    fontSize: '12px',
  },
  typeBadge: {
    padding: '4px 8px',
    background: '#e9ecef',
    color: '#495057',
    borderRadius: '4px',
    fontSize: '12px',
  },
  resourceTitle: {
    fontSize: '16px',
    margin: 0,
  },
  cta: {
    marginTop: '20px',
    padding: '15px',
    background: '#e7f3ff',
    borderRadius: '8px',
    textAlign: 'center' as const,
  },
  empty: {
    padding: '20px',
    textAlign: 'center' as const,
    color: '#666',
  },
}
