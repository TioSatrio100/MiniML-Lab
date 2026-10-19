import { useState } from 'react'
import { ArrowLeft, Circle, Loader2, Moon, Sun } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import ProviderDialog from '@/components/ProviderDialog'
import { api, type SessionConfig } from '@/lib/api'
import { cancelRun, runAgent } from '@/lib/runAgent'
import { useStore } from '@/lib/store'

const TASKS = [
  { value: 'classification', label: 'Classification' },
  { value: 'regression', label: 'Regression' },
  { value: 'clustering', label: 'Clustering' },
  { value: 'recommendation', label: 'Recommendation' },
] as const

const labelCls = 'font-mono text-[11px] uppercase tracking-wider text-muted-foreground'

function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'))

  const toggle = () => {
    const next = !dark
    document.documentElement.classList.toggle('dark', next)
    try {
      localStorage.setItem('miniml-theme', next ? 'dark' : 'light')
    } catch {
      /* storage unavailable */
    }
    setDark(next)
  }

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      onClick={toggle}
      aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
    >
      {dark ? <Sun /> : <Moon />}
    </Button>
  )
}

export default function Sidebar() {
  const config = useStore((s) => s.config)
  const providers = useStore((s) => s.providers)
  const setConfig = useStore((s) => s.setConfig)
  const refreshProviders = useStore((s) => s.refreshProviders)
  const running = useStore((s) => s.running)

  const [apiKey, setApiKey] = useState('')

  const provider = providers.find((p) => p.name === config?.provider) ?? null
  // derived during render — no effect churn when provider list updates
  const keySaved = provider?.has_key ?? false

  if (!config) return null

  const saveKey = async () => {
    if (!apiKey.trim() || !config.provider) return
    await api.updateProvider(config.provider, { api_key: apiKey.trim() })
    await refreshProviders()
    setApiKey('')
  }

  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-border bg-card px-5 py-6 lg:w-72 lg:border-r lg:border-b-0">
      <div className="mb-6 flex items-start justify-between gap-2">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            agent
          </div>
          <div className="text-lg font-bold text-foreground">Configuration</div>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon-sm" asChild aria-label="Back to home page">
            <Link to="/">
              <ArrowLeft />
            </Link>
          </Button>
          <ThemeToggle />
        </div>
      </div>

      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-1.5">
          <Label className={labelCls}>Provider</Label>
          <Select value={config.provider} onValueChange={(v) => setConfig({ provider: v })}>
            <SelectTrigger>
              <SelectValue placeholder="Provider" />
            </SelectTrigger>
            <SelectContent>
              {providers.map((p) => (
                <SelectItem key={p.name} value={p.name}>
                  {p.name}
                  {p.has_key ? ' ✓' : ''}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label className={labelCls}>Model</Label>
          <Select value={config.model_name} onValueChange={(v) => setConfig({ model_name: v })}>
            <SelectTrigger>
              <SelectValue placeholder="Model" />
            </SelectTrigger>
            <SelectContent>
              {(provider?.models ?? []).map((m) => (
                <SelectItem key={m} value={m}>
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label className={labelCls}>
            API key {keySaved ? <span className="text-green-700 dark:text-green-400">saved</span> : null}
          </Label>
          <div className="flex gap-2">
            <Input
              type="password"
              placeholder="sk-…"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="font-mono text-xs"
            />
            <Button variant="outline" size="sm" onClick={saveKey} disabled={!apiKey.trim()}>
              Save
            </Button>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label className={labelCls}>Task</Label>
          <Select value={config.task_type} onValueChange={(v) => setConfig({ task_type: v as SessionConfig['task_type'] })}>
            <SelectTrigger>
              <SelectValue placeholder="Task" />
            </SelectTrigger>
            <SelectContent>
              {TASKS.map((t) => (
                <SelectItem key={t.value} value={t.value}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label className={labelCls}>Max iterations: {config.max_iterations}</Label>
          <input
            type="range"
            min={1}
            max={10}
            value={config.max_iterations}
            onChange={(e) => setConfig({ max_iterations: Number(e.target.value) })}
            className="accent-primary"
          />
        </div>
      </div>

      <div className="mt-auto flex flex-col gap-3 pt-6">
        <ProviderDialog />
        {running ? (
          <Button variant="outline" onClick={cancelRun}>
            Stop
          </Button>
        ) : (
          <Button onClick={() => runAgent()}>Run Auto-ML Loop</Button>
        )}
        <Badge
          variant="outline"
          className={`w-fit font-mono text-[10px] uppercase ${
            running
              ? 'border-green-600/50 text-green-700 dark:border-green-400/50 dark:text-green-400'
              : 'text-muted-foreground'
          }`}
        >
          {running ? <Loader2 className="animate-spin" /> : <Circle />}
        </Badge>
      </div>
    </aside>
  )
}
