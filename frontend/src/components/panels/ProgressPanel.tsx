import { useEffect, useState } from 'react'
import { Star } from 'lucide-react'
import MetricChart from '@/components/charts/MetricChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api, type ProgressResponse } from '@/lib/api'
import { useStore } from '@/lib/store'

const HIGHER_IS_BETTER: Record<string, boolean> = {
  classification: true,
  regression: true,
  clustering: true,
  recommendation: false,
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card size="sm">
      <CardHeader className="pb-0">
        <CardTitle className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent className="font-mono text-2xl font-bold text-foreground">{value}</CardContent>
    </Card>
  )
}

interface IterationCard {
  status: string
  metrics?: Record<string, number>
  is_better?: boolean
  best_score?: number
  error?: string
}

function IterationRow({ n, it }: { n: number; it: IterationCard }) {
  const ok = it.status === 'success'
  return (
    <div
      className={`flex items-start gap-3 rounded-lg border px-4 py-3 transition-colors ${
        ok
          ? 'border-border bg-card hover:bg-muted/60'
          : 'border-destructive/40 bg-destructive/10'
      }`}
    >
      <span className="font-mono text-xs font-semibold text-muted-foreground">#{n}</span>
      <span
        className={`rounded-full px-2 py-0.5 font-mono text-[10px] uppercase ${
          ok ? 'bg-green-500/10 text-green-700 dark:text-green-400' : 'bg-destructive/10 text-destructive'
        }`}
      >
        {it.status}
      </span>
      <div className="flex flex-1 flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-foreground">
        {ok &&
          Object.entries(it.metrics ?? {}).map(([k, v]) => (
            <span key={k}>
              {k}: <b>{typeof v === 'number' ? v.toFixed(4) : String(v)}</b>
            </span>
          ))}
        {!ok && <span className="break-all text-destructive">{it.error}</span>}
      </div>
      {ok && (
        <span className="shrink-0 font-mono text-xs">
          {it.is_better ? (
            <b className="inline-flex items-center gap-1 text-primary">
              <Star className="size-3 fill-current" />
              NEW BEST
            </b>
          ) : (
            <span className="text-muted-foreground">
              best: {typeof it.best_score === 'number' ? it.best_score.toFixed(4) : '-'}
            </span>
          )}
        </span>
      )}
    </div>
  )
}

export default function ProgressPanel() {
  const sessionId = useStore((s) => s.sessionId)
  const config = useStore((s) => s.config)
  const trace = useStore((s) => s.trace)
  const liveIters = useStore((s) => s.iterations)
  const summary = useStore((s) => s.summary)
  const running = useStore((s) => s.running)

  const [progress, setProgress] = useState<ProgressResponse | null>(null)

  useEffect(() => {
    if (!sessionId) return
    api
      .progress(sessionId)
      .then(setProgress)
      .catch(() => setProgress(null))
  }, [sessionId, trace, running, summary])

  const stats = progress?.stats
  const experiments = progress?.experiments ?? []
  const task = config?.task_type ?? 'classification'
  const metric = stats?.metric ?? 'accuracy'
  const metricLabel = stats?.metric_label ?? 'Score'
  const higher = HIGHER_IS_BETTER[task] ?? true

  const historyRows: IterationCard[] = experiments
    .filter((e) => typeof e === 'object' && e !== null)
    .map((e) => {
      const rec = e as { success?: boolean; metrics?: Record<string, number>; error?: string; iteration?: number }
      return rec.success
        ? { status: 'success', metrics: rec.metrics }
        : { status: 'failed', error: rec.error }
    })
  const rows = running || liveIters.length > historyRows.length ? liveIters : historyRows

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <StatCard label="Experiments" value={stats ? `${stats.successful}/${stats.total}` : '-'} />
        <StatCard label="Best score" value={stats?.best_score ? stats.best_score.toFixed(4) : '-'} />
        <StatCard
          label="Improvement"
          value={stats ? `${stats.improvement >= 0 ? '+' : ''}${stats.improvement.toFixed(4)}` : '-'}
        />
        <StatCard label="Best model" value={stats?.best_model_name || 'None'} />
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Metric evolution</CardTitle>
        </CardHeader>
        <CardContent>
          <MetricChart
            experiments={experiments as never}
            metric={metric}
            metricLabel={metricLabel}
            higherIsBetter={higher}
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="flex flex-col gap-3 lg:col-span-3">
          <div className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
            Iterations {running && <span className="text-green-700 dark:text-green-400">live</span>}
          </div>
          {rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No runs yet. Configure and hit Run.</p>
          ) : (
            rows.map((it, i) => <IterationRow key={i} n={i + 1} it={it} />)
          )}
        </div>

        <div className="flex flex-col gap-4 lg:col-span-2">
          {summary && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Final summary</CardTitle>
              </CardHeader>
              <CardContent className="text-sm leading-relaxed text-muted-foreground">{summary}</CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Agent trace</CardTitle>
            </CardHeader>
            <CardContent>
              {trace.length === 0 ? (
                <p className="text-sm text-muted-foreground">Nothing yet. Trace lines appear when a run starts.</p>
              ) : (
                <div className="max-h-96 overflow-y-auto font-mono text-[11px] leading-relaxed text-foreground">
                  {trace.map((line, i) => (
                    <div key={i} className="border-b border-dashed border-border py-1 break-words">
                      {line}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
