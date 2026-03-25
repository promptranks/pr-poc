/**
 * PECAM Radar Chart — Matrix green theme.
 * Pure SVG, no external dependencies.
 */

interface PillarData {
  kba: number
  ppa: number
  combined: number
}

interface RadarChartProps {
  pillarScores: Record<string, PillarData>
  size?: number
}

const PILLARS = ['P', 'E', 'C', 'A', 'M']
const PILLAR_LABELS: Record<string, string> = {
  P: 'Precision',
  E: 'Efficiency',
  C: 'Creativity',
  A: 'Adaptability',
  M: 'Mastery',
}

export default function RadarChart({ pillarScores, size = 300 }: RadarChartProps) {
  const cx = size / 2
  const cy = size / 2
  const maxRadius = size * 0.38
  const labelRadius = size * 0.46
  const levels = [20, 40, 60, 80, 100]
  const angleStep = (2 * Math.PI) / PILLARS.length
  const startAngle = -Math.PI / 2 // Start from top

  const getPoint = (index: number, value: number): [number, number] => {
    const angle = startAngle + index * angleStep
    const r = (value / 100) * maxRadius
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)]
  }

  // Grid lines
  const gridPaths = levels.map((level) => {
    const points = PILLARS.map((_, i) => getPoint(i, level))
    return points.map(([x, y]) => `${x},${y}`).join(' ')
  })

  // Axis lines
  const axes = PILLARS.map((_, i) => getPoint(i, 100))

  // Data polygon
  const dataPoints = PILLARS.map((p, i) => {
    const score = pillarScores[p]?.combined ?? 0
    return getPoint(i, score)
  })
  const dataPath = dataPoints.map(([x, y]) => `${x},${y}`).join(' ')

  // Label positions
  const labelPositions = PILLARS.map((_, i) => {
    const angle = startAngle + i * angleStep
    return [cx + labelRadius * Math.cos(angle), cy + labelRadius * Math.sin(angle)]
  })

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      style={{ display: 'block', margin: '0 auto' }}
    >
      {/* Background */}
      <rect width={size} height={size} fill="transparent" />

      {/* Grid polygons */}
      {gridPaths.map((points, i) => (
        <polygon
          key={`grid-${i}`}
          points={points}
          fill="none"
          stroke="rgba(0,255,65,0.12)"
          strokeWidth={1}
        />
      ))}

      {/* Axis lines */}
      {axes.map(([x, y], i) => (
        <line
          key={`axis-${i}`}
          x1={cx}
          y1={cy}
          x2={x}
          y2={y}
          stroke="rgba(0,255,65,0.15)"
          strokeWidth={1}
        />
      ))}

      {/* Data fill */}
      <polygon
        points={dataPath}
        fill="rgba(0,255,65,0.15)"
        stroke="#00ff41"
        strokeWidth={2}
        style={{
          filter: 'drop-shadow(0 0 6px rgba(0,255,65,0.4))',
        }}
      />

      {/* Data points */}
      {dataPoints.map(([x, y], i) => (
        <circle
          key={`point-${i}`}
          cx={x}
          cy={y}
          r={4}
          fill="#00ff41"
          stroke="#000"
          strokeWidth={1}
          style={{
            filter: 'drop-shadow(0 0 4px rgba(0,255,65,0.6))',
          }}
        />
      ))}

      {/* Labels */}
      {labelPositions.map(([x, y], i) => {
        const pillar = PILLARS[i]
        const score = Math.round(pillarScores[pillar]?.combined ?? 0)
        return (
          <g key={`label-${i}`}>
            <text
              x={x}
              y={y - 8}
              textAnchor="middle"
              dominantBaseline="middle"
              fill="#00ff41"
              fontSize="11"
              fontFamily="'Press Start 2P', monospace"
              style={{
                filter: 'drop-shadow(0 0 4px rgba(0,255,65,0.3))',
              }}
            >
              {pillar}
            </text>
            <text
              x={x}
              y={y + 8}
              textAnchor="middle"
              dominantBaseline="middle"
              fill="#008f11"
              fontSize="9"
              fontFamily="'Share Tech Mono', monospace"
            >
              {score}%
            </text>
          </g>
        )
      })}

      {/* Level labels on the P axis */}
      {levels.map((level) => {
        const [x, y] = getPoint(0, level)
        return (
          <text
            key={`level-${level}`}
            x={x + 8}
            y={y}
            fill="rgba(0,255,65,0.3)"
            fontSize="8"
            fontFamily="'Share Tech Mono', monospace"
            dominantBaseline="middle"
          >
            {level}
          </text>
        )
      })}
    </svg>
  )
}

export { PILLAR_LABELS }
