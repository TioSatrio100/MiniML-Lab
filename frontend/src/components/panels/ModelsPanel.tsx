import { useEffect, useState } from 'react'
import { Check, Code2, Download, Pencil, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { api, type ModelInfo } from '@/lib/api'
import { useStore } from '@/lib/store'

export default function ModelsPanel() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [error, setError] = useState<string | null>(null)
  const [code, setCode] = useState<{ name: string; code: string } | null>(null)
  const [compare, setCompare] = useState<string[]>([])
  const [renaming, setRenaming] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const modelsVersion = useStore((s) => s.modelsVersion)

  const refresh = () => api.models().then(setModels).catch((e) => setError(String(e.message ?? e)))

  useEffect(() => {
    refresh()
  }, [modelsVersion])

  if (error) return <p className="text-sm text-destructive">{error}</p>
  if (models.length === 0)
    return (
      <p className="text-sm text-muted-foreground">
        No saved models yet. The agent registers the best one via save_model.
      </p>
    )

  const selected = compare
    .map((n) => models.find((m) => m.model_name === n))
    .filter((m): m is ModelInfo => Boolean(m))

  const metricKeys = [...new Set(selected.flatMap((m) => Object.keys(m.metrics)))]

  const toggleCompare = (name: string) => {
    setCompare((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : prev.length >= 3 ? [...prev.slice(1), name] : [...prev, name],
    )
  }

  const startRename = (m: ModelInfo) => {
    setRenaming(m.model_name)
    setRenameValue(m.display_name || m.model_name)
  }

  const commitRename = async (model_name: string) => {
    const value = renameValue.trim()
    setRenaming(null)
    if (!value) return
    try {
      await api.renameModel(model_name, value)
      await refresh()
    } catch (e) {
      setError(String((e as Error).message ?? e))
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          select up to 3 to compare
        </span>
        {compare.length > 1 && (
          <span className="font-mono text-[11px] text-primary">{compare.length} selected</span>
        )}
      </div>

      {selected.length > 1 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Compare</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full border-collapse font-mono text-xs">
              <thead>
                <tr className="bg-muted text-left text-muted-foreground">
                  <th className="border-b border-border px-3 py-2 font-medium">metric</th>
                  {selected.map((m) => (
                    <th key={m.model_name} className="border-b border-border px-3 py-2 font-medium">
                      {m.display_name || m.model_name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metricKeys.map((k) => (
                  <tr key={k} className="odd:bg-card even:bg-muted/50">
                    <td className="border-b border-dashed border-border px-3 py-1.5 text-muted-foreground">{k}</td>
                    {selected.map((m) => {
                      const v = m.metrics[k]
                      const vals = selected.map((s) => s.metrics[k]).filter((x) => typeof x === 'number') as number[]
                      const bestVal = vals.length ? Math.max(...vals) : null
                      const isBest = typeof v === 'number' && v === bestVal
                      return (
                        <td
                          key={m.model_name}
                          className={`border-b border-dashed border-border px-3 py-1.5 ${
                            isBest ? 'font-bold text-primary' : 'text-foreground'
                          }`}
                        >
                          {typeof v === 'number' ? v.toFixed(4) : '-'}
                        </td>
                      )
                    })}
                  </tr>
                ))}
                <tr>
                  <td className="px-3 py-1.5 text-muted-foreground">saved</td>
                  {selected.map((m) => (
                    <td key={m.model_name} className="px-3 py-1.5 text-muted-foreground">
                      {m.saved_at}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      {models.map((m) => (
        <Card key={m.model_name} className={compare.includes(m.model_name) ? 'border-primary' : ''}>
          <CardHeader className="flex-row items-center justify-between gap-3 pb-2">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={compare.includes(m.model_name)}
                onChange={() => toggleCompare(m.model_name)}
                className="accent-primary"
                aria-label={`compare ${m.model_name}`}
              />
              {renaming === m.model_name ? (
                <form
                  className="flex items-center gap-1"
                  onSubmit={(e) => {
                    e.preventDefault()
                    void commitRename(m.model_name)
                  }}
                >
                  <Input
                    autoFocus
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    onBlur={() => commitRename(m.model_name)}
                    onKeyDown={(e) => e.key === 'Escape' && setRenaming(null)}
                    className="h-7 w-48 font-mono text-xs"
                    aria-label="new model name"
                  />
                  <Button type="submit" variant="ghost" size="icon-sm" aria-label="confirm rename">
                    <Check className="size-3.5" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => setRenaming(null)}
                    aria-label="cancel rename"
                  >
                    <X className="size-3.5" />
                  </Button>
                </form>
              ) : (
                <>
                  <CardTitle className="font-mono text-sm">{m.display_name || m.model_name}</CardTitle>
                  <button
                    className="text-muted-foreground transition-colors hover:text-primary"
                    onClick={() => startRename(m)}
                    aria-label={`rename ${m.model_name}`}
                  >
                    <Pencil className="size-3" />
                  </button>
                </>
              )}
            </div>
            <div className="flex gap-4 font-mono text-xs">
              <button
                className="inline-flex items-center gap-1 text-primary transition-colors hover:underline"
                onClick={() =>
                  api
                    .modelCode(m.model_name)
                    .then((r) => setCode({ name: r.model_name, code: r.code }))
                    .catch(() => setCode(null))
                }
              >
                <Code2 className="size-3.5" />
                code
              </button>
              <a
                className="inline-flex items-center gap-1 text-primary transition-colors hover:underline"
                href={`/api/models/${encodeURIComponent(m.model_name)}/download`}
                download={`${m.model_name}.pkl`}
              >
                <Download className="size-3.5" />
                download
              </a>
            </div>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-4 font-mono text-xs text-muted-foreground">
            {Object.entries(m.metrics).map(([k, v]) => (
              <span key={k}>
                {k}: <b className="text-foreground">{typeof v === 'number' ? v.toFixed(4) : String(v)}</b>
              </span>
            ))}
            <span>saved: {m.saved_at}</span>
          </CardContent>
        </Card>
      ))}

      {code && (
        <Card>
          <CardHeader className="flex-row items-center justify-between pb-2">
            <CardTitle className="font-mono text-sm">code for {code.name}</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => setCode(null)}>
              close
            </Button>
          </CardHeader>
          <CardContent>
            <pre className="max-h-96 overflow-auto rounded-lg border border-border bg-muted p-4 font-mono text-xs text-foreground">
              {code.code}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
