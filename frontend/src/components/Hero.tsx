import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { useStore } from '@/lib/store'

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted-foreground">{label}</span>
      <span className="font-mono text-base font-semibold text-foreground">{value}</span>
    </div>
  )
}

export default function Hero() {
  const bestScore = useStore((s) => s.bestScore)
  const bestModelName = useStore((s) => s.bestModelName)
  const iterations = useStore((s) => s.iterations)
  const sessionId = useStore((s) => s.sessionId)
  const [progressImp, setProgressImp] = useState<number | null>(null)

  // server-computed improvement survives page-reload mid-history (no recompute drift)
  useEffect(() => {
    if (!sessionId) return
    api
      .progress(sessionId)
      .then((r) => setProgressImp(r.stats.improvement))
      .catch(() => setProgressImp(null))
  }, [sessionId, iterations.length])

  const improvement = progressImp ?? 0

  return (
    <header className="mb-6 flex flex-col gap-4 border-b border-border pb-6 md:flex-row md:items-end md:justify-between">
      <div>
        <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
          autonomous ml lab
        </div>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">MiniML Lab</h1>
        <p className="mt-1 max-w-[52ch] text-sm leading-relaxed text-muted-foreground">
          Configure your agent, prepare your dataset, and watch it search for the best model, one
          experiment at a time.
        </p>
      </div>

      <div className="flex shrink-0 gap-8">
        <Stat label="Best score" value={bestScore ? bestScore.toFixed(4) : '-'} />
        <Stat
          label="Improvement"
          value={`${improvement >= 0 ? '+' : ''}${improvement.toFixed(4)}`}
        />
        <Stat label="Best model" value={bestModelName || '-'} />
      </div>
    </header>
  )
}
