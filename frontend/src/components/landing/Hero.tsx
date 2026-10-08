import { motion, useReducedMotion } from 'motion/react'
import { Link } from 'react-router-dom'
import MetricChart from '@/components/charts/MetricChart'
import { Button } from '@/components/ui/button'

const sampleExperiments = [
  { iteration: 1, success: true, metrics: { val_f1: 0.612 } },
  { iteration: 2, success: true, metrics: { val_f1: 0.648 } },
  { iteration: 3, success: true, metrics: { val_f1: 0.631 } },
  { iteration: 4, success: false, error: 'estimator rejected C=0.001' },
  { iteration: 5, success: true, metrics: { val_f1: 0.674 } },
  { iteration: 6, success: true, metrics: { val_f1: 0.703 } },
]

export default function Hero() {
  const reduce = useReducedMotion()
  const rise = (delay: number) => ({
    initial: reduce ? false : { opacity: 0, y: 24 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.7, delay, ease: [0.16, 1, 0.3, 1] as const },
  })

  return (
    <section className="mx-auto w-full max-w-7xl px-6 pt-14 pb-20 lg:pt-24">
      <div className="grid items-center gap-10 lg:grid-cols-[1.05fr_1fr]">
        <div>
          <motion.p
            {...rise(0)}
            className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground"
          >
            autonomous ml lab
          </motion.p>

          <motion.h1
            {...rise(0.08)}
            className="mt-4 max-w-[20ch] text-4xl font-bold tracking-tighter text-foreground sm:text-5xl lg:text-6xl"
          >
            Run an Auto-ML loop, not a notebook.
          </motion.h1>

          <motion.p
            {...rise(0.16)}
            className="mt-5 max-w-[52ch] text-base leading-relaxed text-muted-foreground"
          >
            Configure a provider, pick a task, and let the agent search models and hyperparameters
            while every experiment streams live.
          </motion.p>

          <motion.div {...rise(0.24)} className="mt-7 flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <Link to="/app">Open dashboard</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <a href="#how">See how it works</a>
            </Button>
          </motion.div>
        </div>

        <motion.div
          {...rise(0.3)}
          className="rounded-xl bg-card p-5 ring-1 ring-foreground/10"
        >
          <div className="mb-3 flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              val_f1 evolution
            </span>
            <span className="font-mono text-[10px] text-green-700 dark:text-green-400">
              best 0.7030
            </span>
          </div>
          <MetricChart
            experiments={sampleExperiments}
            metric="val_f1"
            metricLabel="val_f1"
            higherIsBetter
          />
          <p className="mt-3 border-t border-dashed border-border pt-3 text-xs text-muted-foreground">
            Sample run. Your live charts look the same.
          </p>
        </motion.div>
      </div>
    </section>
  )
}
