import { useEffect, useRef, useState } from 'react'
import { Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { api, type DataPreview, type SessionConfig } from '@/lib/api'
import { useStore } from '@/lib/store'

const TASKS = ['classification', 'regression', 'clustering', 'recommendation']

const SYNTHETIC_UNSUPPORTED = ['clustering', 'recommendation']

export default function DataPanel() {
  const sessionId = useStore((s) => s.sessionId)
  const config = useStore((s) => s.config)
  const setConfig = useStore((s) => s.setConfig)

  const [preview, setPreview] = useState<DataPreview | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [nSamples, setNSamples] = useState(200)
  const [nFeatures, setNFeatures] = useState(10)
  const [aiDescription, setAiDescription] = useState('')
  const [aiBusy, setAiBusy] = useState(false)
  const [aiCode, setAiCode] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const syntheticBlocked = SYNTHETIC_UNSUPPORTED.includes(config?.task_type ?? 'classification')

  useEffect(() => {
    if (!sessionId) return
    api.preview(sessionId).then(setPreview).catch(() => setPreview(null))
  }, [sessionId])

  const generateAI = async () => {
    if (!sessionId || !aiDescription.trim() || aiBusy) return
    setAiBusy(true)
    setError(null)
    try {
      const r = await api.generateAIData(sessionId, aiDescription.trim(), nSamples)
      setPreview(r.preview)
      setAiCode(r.code)
    } catch (e) {
      setError(String((e as Error).message ?? e))
    } finally {
      setAiBusy(false)
    }
  }

  const generate = async () => {
    if (!sessionId || syntheticBlocked) return
    setBusy(true)
    setError(null)
    try {
      const r = await api.generateSynthetic(sessionId, config?.task_type ?? 'classification', nSamples, nFeatures)
      setPreview(r.preview)
      await setConfig({ n_samples: nSamples, n_features: nFeatures })
    } catch (e) {
      setError(String((e as Error).message ?? e))
    } finally {
      setBusy(false)
    }
  }

  const upload = async (file: File) => {
    if (!sessionId) return
    setBusy(true)
    setError(null)
    try {
      const r = await api.uploadCsv(sessionId, file)
      setPreview(r.preview)
    } catch (e) {
      setError(String((e as Error).message ?? e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Synthetic data</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="flex gap-3">
              <div className="flex-1">
                <Label className="font-mono text-[10px] uppercase text-muted-foreground">Samples</Label>
                <Input
                  type="number"
                  value={nSamples}
                  min={10}
                  onChange={(e) => setNSamples(Number(e.target.value))}
                  className="font-mono text-xs"
                />
              </div>
              <div className="flex-1">
                <Label className="font-mono text-[10px] uppercase text-muted-foreground">Features</Label>
                <Input
                  type="number"
                  value={nFeatures}
                  min={2}
                  onChange={(e) => setNFeatures(Number(e.target.value))}
                  className="font-mono text-xs"
                />
              </div>
            </div>
            <div className="flex gap-3">
              <Select value={config?.task_type ?? 'classification'} onValueChange={(v) => setConfig({ task_type: v as SessionConfig['task_type'] })}>
                <SelectTrigger className="flex-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TASKS.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button onClick={generate} disabled={busy} title={syntheticBlocked ? 'Switch to classification/regression, or upload CSV / use AI data for this task' : undefined}>
                Generate
              </Button>
            </div>
            {syntheticBlocked && (
              <p className="text-xs text-amber-600 dark:text-amber-400">
                Synthetic data unavailable for {config?.task_type} — upload a CSV or use AI-generated data.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Upload CSV</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
            />
            <p className="text-xs text-muted-foreground">
              Target column auto-detected (last col or 'target').
            </p>
            <Button variant="outline" onClick={() => fileRef.current?.click()} disabled={busy}>
              Choose file…
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Sparkles className="size-4 text-primary" />
              AI-generated data
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div>
              <Label className="font-mono text-[10px] uppercase text-muted-foreground">Describe the dataset</Label>
              <Textarea
                value={aiDescription}
                onChange={(e) => setAiDescription(e.target.value)}
                placeholder={
                  config?.task_type === 'clustering'
                    ? 'e.g. mall customers with spending score and income forming ~5 groups'
                    : config?.task_type === 'recommendation'
                      ? 'e.g. 300 movies with genre, runtime, popularity and viewer ratings 1-5'
                      : 'e.g. sensor readings predicting machine failure'
                }
                className="min-h-[64px] font-mono text-xs"
               />
            </div>
            <Button onClick={() => void generateAI()} disabled={aiBusy || !aiDescription.trim()}>
              {aiBusy ? 'Generating…' : 'Generate with AI'}
            </Button>
            {aiCode && (
              <details className="font-mono text-[11px]">
                <summary className="cursor-pointer text-muted-foreground">generated script</summary>
                <pre className="mt-2 max-h-48 overflow-auto rounded-lg border border-border bg-muted p-3 text-[11px] text-foreground">
                  {aiCode}
                </pre>
              </details>
            )}
          </CardContent>
        </Card>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Card>
        <CardHeader className="flex-row items-center justify-between gap-3 pb-2">
          <CardTitle className="text-sm">Dataset preview</CardTitle>
          {preview?.has_data && (
            <span className="font-mono text-xs text-muted-foreground">
              {preview.shape?.[0]} rows × {preview.shape?.[1]} cols, target: {preview.target ?? '-'}
            </span>
          )}
        </CardHeader>
        <CardContent>
          {!preview?.has_data ? (
            <p className="text-sm text-muted-foreground">
              No dataset yet. Generate or upload one.
            </p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full border-collapse font-mono text-xs">
                <thead>
                  <tr className="bg-muted text-left text-muted-foreground">
                    {preview.columns?.map((c) => (
                      <th key={c} className="border-b border-border px-3 py-2 font-medium">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(preview.rows ?? []).map((row, i) => (
                    <tr key={i} className="odd:bg-card even:bg-muted/50">
                      {preview.columns?.map((c) => (
                        <td key={c} className="border-b border-dashed border-border px-3 py-1.5 text-foreground">
                          {formatCell(row[c])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function formatCell(v: unknown): string {
  if (v === null || v === undefined) return '-'
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : v.toFixed(4)
  return String(v)
}
