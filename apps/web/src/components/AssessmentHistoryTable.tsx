import { useNavigate } from 'react-router-dom'

interface Assessment {
  id: string
  mode: string
  final_score: number | null
  level: number | null
  status: string
  results_locked: boolean
  completed_at: string | null
}

interface AssessmentHistoryTableProps {
  assessments: Assessment[]
}

export default function AssessmentHistoryTable({ assessments }: AssessmentHistoryTableProps) {
  const navigate = useNavigate()

  if (assessments.length === 0) {
    return <p style={styles.empty}>No assessments yet. Start your first assessment!</p>
  }

  const handleRowClick = (assessment: Assessment) => {
    if (assessment.status === 'completed' && !assessment.results_locked) {
      navigate(`/dashboard/assessment/${assessment.id}`)
    }
  }

  return (
    <table style={styles.table}>
      <thead>
        <tr>
          <th style={styles.th}>Date</th>
          <th style={styles.th}>Mode</th>
          <th style={styles.th}>Score</th>
          <th style={styles.th}>Level</th>
          <th style={styles.th}>Status</th>
        </tr>
      </thead>
      <tbody>
        {assessments.map((assessment) => {
          const isClickable = assessment.status === 'completed' && !assessment.results_locked
          return (
            <tr
              key={assessment.id}
              style={{
                ...styles.tr,
                ...(isClickable ? styles.clickableRow : {}),
              }}
              onClick={() => handleRowClick(assessment)}
            >
              <td style={styles.td}>
                {assessment.completed_at
                  ? new Date(assessment.completed_at).toLocaleDateString()
                  : 'In Progress'}
              </td>
              <td style={styles.td}>
                {assessment.mode === 'quick' ? 'Quick' : 'Full'}
              </td>
              <td style={styles.td}>
                {assessment.results_locked ? '🔒 Locked' : assessment.final_score?.toFixed(1) || '-'}
              </td>
              <td style={styles.td}>
                {assessment.results_locked ? '-' : assessment.level || '-'}
              </td>
              <td style={styles.td}>
                <span style={getStatusStyle(assessment.status)}>
                  {assessment.status.replace('_', ' ')}
                </span>
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

function getStatusStyle(status: string) {
  const baseStyle = {
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.8rem',
    fontFamily: "'Courier New', monospace",
  }
  if (status === 'completed') return { ...baseStyle, background: 'transparent', color: '#00ff41', border: '1px solid #00ff41' }
  if (status === 'in_progress') return { ...baseStyle, background: 'transparent', color: '#ffaa00', border: '1px solid #ffaa00' }
  return { ...baseStyle, background: 'transparent', color: '#ff4444', border: '1px solid #ff4444' }
}

const styles = {
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    marginTop: '1rem',
    fontFamily: "'Courier New', monospace",
  },
  th: {
    textAlign: 'left' as const,
    padding: '0.75rem',
    borderBottom: '1px solid #00ff41',
    fontWeight: 'bold' as const,
    color: '#00ff41',
    fontSize: '0.9rem',
  },
  tr: {
    borderBottom: '1px solid #1a1a1a',
  },
  clickableRow: {
    cursor: 'pointer',
    transition: 'background-color 0.2s',
    backgroundColor: 'transparent',
  },
  td: {
    padding: '0.75rem',
    color: '#00ff41',
    fontSize: '0.9rem',
  },
  empty: {
    textAlign: 'center' as const,
    color: '#008f11',
    padding: '2rem',
    fontFamily: "'Courier New', monospace",
  },
}
