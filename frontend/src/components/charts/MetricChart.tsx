/**
 * MetricChart.tsx - SVG metric-evolution chart (no chart lib).
 * Points = successful experiments; star = best; theme colors from CSS vars.
 */
export interface ChartExperiment {
  iteration?: number
  success?: boolean
  metrics?: Record<string, number>
}

interface Props {
  experiments: ChartExperiment[]
  metric: string
  metricLabel: string
  higherIsBetter: boolean
}

const W = 720
const H = 240
const PAD = { top: 24, right: 24, bottom: 36, left: 56 }

export default function MetricChart({ experiments, metric, metricLabel, higherIsBetter }: Props) {
  const pts = experiments
    .map((e, i) => ({ i: i + 1, v: e.metrics?.[metric] }))
    .filter((p): p is { i: number; v: number } => typeof p.v === 'number')

  if (pts.length === 0) {
    return (
      <div className="flex h-[240px] items-center justify-center font-mono text-xs text-muted-foreground">
        no successful experiments yet
      </div>
    )
  }

  const values = pts.map((p) => p.v)
  let lo = Math.min(...values)
  let hi = Math.max(...values)
  if (lo === hi) {
    const d = Math.abs(lo) * 0.1 || 1
    lo -= d
    hi += d
  } else {
    const m = (hi - lo) * 0.1
    lo -= m
    hi += m
  }

  const best = higherIsBetter ? Math.max(...values) : Math.min(...values)
  const xMin = 1
  const xMax = Math.max(pts[pts.length - 1].i, 2)

  const sx = (i: number) =>
    PAD.left + ((i - xMin) / (xMax - xMin)) * (W - PAD.left - PAD.right)
  const sy = (v: number) => PAD.top + (1 - (v - lo) / (hi - lo)) * (H - PAD.top - PAD.bottom)

  const yTicks = Array.from({ length: 4 }, (_, k) => lo + ((hi - lo) * k) / 3)
  const linePts = pts.map((p) => `${sx(p.i)},${sy(p.v)}`).join(' ')

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="metric evolution">
      {yTicks.map((t) => (
        <g key={t}>
          <line
            x1={PAD.left}
            x2={W - PAD.right}
            y1={sy(t)}
            y2={sy(t)}
            stroke="var(--border)"
            strokeDasharray="3 4"
          />
          <text x={PAD.left - 8} y={sy(t) + 3} textAnchor="end" fontSize="10" fill="var(--muted-foreground)" fontFamily="JetBrains Mono">
            {t.toFixed(3)}
          </text>
        </g>
      ))}

      <polyline points={linePts} fill="none" stroke="var(--primary)" strokeWidth="2" />

      {pts.map((p) => {
        const isBest = p.v === best
        return (
          <g key={p.i}>
            {isBest && (
              <circle cx={sx(p.i)} cy={sy(p.v)} r="8" fill="none" stroke="var(--primary)" strokeWidth="1.5" opacity="0.5" />
            )}
            <circle
              cx={sx(p.i)}
              cy={sy(p.v)}
              r={isBest ? 4.5 : 3}
              fill={isBest ? 'var(--primary)' : 'var(--foreground)'}
            >
              <title>{`iter ${p.i}: ${metricLabel} = ${p.v.toFixed(4)}`}</title>
            </circle>
            <text
              x={sx(p.i)}
              y={H - PAD.bottom + 16}
              textAnchor="middle"
              fontSize="10"
              fill="var(--muted-foreground)"
              fontFamily="JetBrains Mono"
            >
              {p.i}
            </text>
          </g>
        )
      })}

      <text
        x={PAD.left}
        y={14}
        fontSize="10"
        fill="var(--muted-foreground)"
        fontFamily="JetBrains Mono"
        letterSpacing="0.05em"
      >
        {metricLabel.toUpperCase()} {higherIsBetter ? '↑' : '↓'}
      </text>
    </svg>
  )
}
