import { Database, KeyRound, PackageCheck, Repeat } from 'lucide-react'
import Reveal from './Reveal'

const steps = [
  {
    icon: KeyRound,
    title: 'Configure',
    body: 'Pick a provider and model, paste an API key. Keys stay on the server, never in the browser.',
  },
  {
    icon: Database,
    title: 'Prepare data',
    body: 'Generate synthetic data or upload a CSV. The target column is detected for you.',
  },
  {
    icon: Repeat,
    title: 'Run the loop',
    body: 'The agent writes experiment code, runs it, and streams every trace line while you watch.',
  },
  {
    icon: PackageCheck,
    title: 'Ship the model',
    body: 'Compare metrics, read the generated code, download the pickle. All from My Models.',
  },
]

export default function HowItWorks() {
  return (
    <section id="how" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto w-full max-w-7xl px-6 py-16 lg:py-24">
        <Reveal className="max-w-2xl">
          <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            From empty session to saved model.
          </h2>
          <p className="mt-4 max-w-[60ch] text-base leading-relaxed text-muted-foreground">
            Four moves, one screen. You stay in control of config and data while the agent handles
            the search.
          </p>
        </Reveal>

        <div className="mt-12 grid gap-8 md:grid-cols-2">
          {steps.map((s, i) => (
            <Reveal key={s.title} delay={i * 0.07} className={i % 2 === 1 ? 'md:mt-12' : undefined}>
              <div className="border-t border-border pt-5">
                <s.icon className="size-5 text-primary" aria-hidden />
                <h3 className="mt-3 font-mono text-sm font-semibold uppercase tracking-wide text-foreground">
                  {s.title}
                </h3>
                <p className="mt-2 max-w-[46ch] text-sm leading-relaxed text-muted-foreground">
                  {s.body}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
