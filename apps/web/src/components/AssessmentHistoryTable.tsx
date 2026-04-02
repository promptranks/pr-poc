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
    // TODO: Create assessment detail page at /dashboard/assessment/:id
    // For now, just navigate to results page if completed
    if (assessment.status === 'completed' && !assessment.results_locked) {
      // Navigate to results page instead since detail page doesn't exist yet
      navigate(`/assessment/${assessment.id}`)
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
  const baseStyle = { padding: '4px 8px', borderRadius: '4px', fontSize: '12px' }
  if (status === 'completed') return { ...baseStyle, background: '#d4edda', color: '#155724' }
  if (status === 'in_progress') return { ...baseStyle, background: '#fff3cd', color: '#856404' }
  return { ...baseStyle, background: '#f8d7da', color: '#721c24' }
}

const styles = {
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    marginTop: '20px',
  },
  th: {
    textAlign: 'left' as const,
    padding: '12px',
    borderBottom: '2px solid #ddd',
    fontWeight: 'bold' as const,
  },
  tr: {
    borderBottom: '1px solid #eee',
  },
  clickableRow: {
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  td: {
    padding: '12px',
  },
  empty: {
    textAlign: 'center' as const,
    color: '#666',
    padding: '40px',
  },
}
