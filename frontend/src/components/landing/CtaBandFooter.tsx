import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import Reveal from './Reveal'

export function CtaBand() {
  return (
    <section className="mx-auto w-full max-w-7xl px-6 pb-16 lg:pb-24">
      <Reveal>
        <div className="relative overflow-hidden rounded-xl px-6 py-14 text-center sm:px-12">
          <img
            src="https://picsum.photos/seed/miniml-workbench/1600/600?grayscale"
            alt=""
            aria-hidden
            loading="lazy"
            className="absolute inset-0 h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-zinc-950/80" aria-hidden />
          <div className="relative mx-auto flex max-w-2xl flex-col items-center gap-5">
            <h2 className="text-3xl font-bold tracking-tight text-zinc-50 sm:text-4xl">
              Watch one run end to end.
            </h2>
            <p className="max-w-[46ch] text-sm leading-relaxed text-zinc-300">
              Open the dashboard, generate a dataset, and start the loop. No signup. Runs locally.
            </p>
            <Button asChild size="lg">
              <Link to="/app">Open dashboard</Link>
            </Button>
          </div>
        </div>
      </Reveal>
    </section>
  )
}

export function Footer() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex w-full max-w-7xl flex-col items-start justify-between gap-4 px-6 py-8 sm:flex-row sm:items-center">
        <div className="flex items-center gap-2.5">
          <span className="flex size-6 items-center justify-center rounded-lg bg-primary font-mono text-xs font-bold text-primary-foreground">
            M
          </span>
          <span className="text-sm font-semibold text-foreground">MiniML Lab</span>
        </div>
        <nav className="flex items-center gap-6 text-xs text-muted-foreground">
          <a href="#how" className="transition-colors hover:text-foreground">
            How it works
          </a>
          <a href="#features" className="transition-colors hover:text-foreground">
            Features
          </a>
          <Link to="/app" className="transition-colors hover:text-foreground">
            Dashboard
          </Link>
        </nav>
      </div>
    </footer>
  )
}
