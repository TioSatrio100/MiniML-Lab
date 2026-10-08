import { useState } from 'react'
import { Radar, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api, type Provider } from '@/lib/api'
import { useStore } from '@/lib/store'

export default function ProviderDialog() {
  const providers = useStore((s) => s.providers)
  const refresh = useStore((s) => s.refreshProviders)

  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [models, setModels] = useState('')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  const addProvider = async () => {
    if (!name.trim() || !baseUrl.trim()) {
      setMsg('name and base_url required')
      return
    }
    setBusy(true)
    setMsg(null)
    try {
      await api.addProvider({
        name: name.trim(),
        base_url: baseUrl.trim(),
        api_key: apiKey.trim(),
        models: models
          .split(',')
          .map((m) => m.trim())
          .filter(Boolean),
      })
      await refresh()
      setMsg(`${name.trim()} added`)
      setName('')
      setBaseUrl('')
      setApiKey('')
      setModels('')
    } catch (e) {
      setMsg(String((e as Error).message ?? e))
    } finally {
      setBusy(false)
    }
  }

  const discover = async (p: Provider) => {
    setMsg(null)
    try {
      const r = await api.discovery(p.name)
      setMsg(`${p.name}: ${r.models.length} models`)
      await refresh()
    } catch (e) {
      setMsg(`${p.name}: ${(e as Error).message ?? e}`)
    }
  }

  const remove = async (p: Provider) => {
    try {
      await api.removeProvider(p.name)
      await refresh()
    } catch (e) {
      setMsg(String((e as Error).message ?? e))
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o)
        if (o) setMsg(null)
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline" className="w-full font-mono text-xs">
          manage providers
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Providers</DialogTitle>
          <DialogDescription className="font-mono text-xs">
            keys stored server-side in storage/providers.json, never returned to the browser
          </DialogDescription>
        </DialogHeader>

        <div className="flex max-h-64 flex-col gap-2 overflow-y-auto">
          {providers.map((p) => (
            <div key={p.name} className="flex items-center gap-2 rounded-lg border border-border px-3 py-2">
              <span className="flex-1 font-mono text-sm">{p.name}</span>
              <Badge variant="outline" className="font-mono text-[10px]">
                {p.models.length} models
              </Badge>
              <Badge
                variant="outline"
                className={`font-mono text-[10px] ${
                  p.has_key ? 'text-green-700 dark:text-green-400' : 'text-destructive'
                }`}
              >
                {p.has_key ? 'key ✓' : 'no key'}
              </Badge>
              <button
                className="inline-flex items-center gap-1 font-mono text-[11px] text-primary transition-colors hover:underline"
                onClick={() => discover(p)}
                title="fetch model list from base_url/models"
              >
                <Radar className="size-3" />
                discover
              </button>
              {p.builtin ? (
                <span className="font-mono text-[10px] text-muted-foreground">builtin</span>
              ) : (
                <button
                  className="inline-flex items-center gap-1 font-mono text-[11px] text-destructive transition-colors hover:underline"
                  onClick={() => remove(p)}
                >
                  <Trash2 className="size-3" />
                  delete
                </button>
              )}
            </div>
          ))}
        </div>

        <div className="border-t border-border pt-4">
          <div className="mb-2 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
            add custom endpoint
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <div>
              <Label className="font-mono text-[10px] text-muted-foreground">name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="my-platform" />
            </div>
            <div>
              <Label className="font-mono text-[10px] text-muted-foreground">base_url</Label>
              <Input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="https://api.x.com/v1" />
            </div>
            <div>
              <Label className="font-mono text-[10px] text-muted-foreground">api_key (optional)</Label>
              <Input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="sk-…" />
            </div>
            <div>
              <Label className="font-mono text-[10px] text-muted-foreground">models (comma-sep)</Label>
              <Input value={models} onChange={(e) => setModels(e.target.value)} placeholder="gpt-4o-mini, llama3" />
            </div>
          </div>
          <div className="mt-3 flex items-center gap-3">
            <Button size="sm" onClick={addProvider} disabled={busy}>
              Add provider
            </Button>
            {msg && <span className="font-mono text-xs text-muted-foreground">{msg}</span>}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
