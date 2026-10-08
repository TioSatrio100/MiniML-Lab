import { useEffect } from 'react'
import Hero from '../components/Hero'
import Sidebar from '../components/Sidebar'
import TabShell from '../components/TabShell'
import { useStore } from '../lib/store'

export default function Dashboard() {
  const init = useStore((s) => s.init)
  const sessionId = useStore((s) => s.sessionId)
  const error = useStore((s) => s.error)

  useEffect(() => {
    init().catch((e) => console.error('session init failed:', e))
  }, [init])

  if (!sessionId) {
    return (
      <div className="flex h-full items-center justify-center font-mono text-sm text-muted-foreground">
        bootstrapping session…
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col lg:flex-row">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-y-auto px-4 py-6 lg:px-8 lg:py-8">
        {error && (
          <div
            role="alert"
            className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive"
          >
            {error}
          </div>
        )}
        <Hero />
        <TabShell />
      </main>
    </div>
  )
}
