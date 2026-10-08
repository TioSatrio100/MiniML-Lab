import { Database, KeyRound, Package, ScrollText, TrendingUp } from 'lucide-react'
import Reveal from './Reveal'

const cells = [
  {
    icon: TrendingUp,
    title: 'Metric evolution chart',
    body: 'Every successful experiment plotted, best point starred.',
    span: 'md:col-span-2',
    bg: 'bg-primary/10',
  },
  {
    icon: Database,
    title: 'Sandbox data lab',
    body: 'Synthetic generators and CSV upload side by side, with a live preview table.',
    span: 'md:col-span-2',
    bg: 'bg-card',
  },
  {
    icon: Package,
    title: 'Model registry',
    body: 'Metrics, generated code, and pickle download for every saved model.',
    span: 'md:col-span-2',
    bg: 'bg-muted',
  },
]

export default function Features() {
  return (
    <section id="features" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto w-full max-w-7xl px-6 py-16 lg:py-24">
        <Reveal className="max-w-2xl">
          <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Everything the dashboard gives you.
          </h2>
          <p className="mt-4 max-w-[60ch] text-base leading-relaxed text-muted-foreground">
            One workspace for config, data, experiments, and the models you keep.
          </p>
        </Reveal>

        <div className="mt-12 grid grid-cols-1 gap-4 md:grid-cols-6">
          <Reveal className="md:col-span-4">
            <div className="flex h-full flex-col gap-4 rounded-xl bg-muted p-6 ring-1 ring-foreground/10">
              <img
                src="https://picsum.photos/seed/miniml-terminal/900/700?grayscale"
                alt="Developer workstation with code on screen"
                loading="lazy"
                className="h-44 w-full rounded-lg object-cover md:h-64"
              />
              <div>
                <h3 className="flex items-center gap-2 font-mono text-sm font-semibold uppercase tracking-wide text-foreground">
                  <ScrollText className="size-4 text-primary" aria-hidden />
                  Trace every agent step
                </h3>
                <p className="mt-2 max-w-[52ch] text-sm leading-relaxed text-muted-foreground">
                  Thought, action, observation, one line each. Failures land inline while the loop
                  is still running.
                </p>
              </div>
            </div>
          </Reveal>

          {cells.map((c, i) => (
            <Reveal key={c.title} delay={i * 0.07} className={c.span}>
              <div className={`flex h-full flex-col gap-3 rounded-xl p-6 ring-1 ring-foreground/10 ${c.bg}`}>
                <c.icon className="size-5 text-primary" aria-hidden />
                <h3 className="font-mono text-sm font-semibold uppercase tracking-wide text-foreground">
                  {c.title}
                </h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{c.body}</p>
              </div>
            </Reveal>
          ))}

          <Reveal className="md:col-span-6">
            <div className="flex flex-col items-start gap-3 rounded-xl bg-primary/10 p-6 ring-1 ring-foreground/10 sm:flex-row sm:items-center">
              <KeyRound className="size-5 shrink-0 text-primary" aria-hidden />
              <div>
                <h3 className="font-mono text-sm font-semibold uppercase tracking-wide text-foreground">
                  Bring your own provider
                </h3>
                <p className="mt-1 max-w-[70ch] text-sm leading-relaxed text-muted-foreground">
                  Built-in OpenAI-compatible presets plus custom endpoints. Discover models from the
                  provider, store keys server-side.
                </p>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  )
}
