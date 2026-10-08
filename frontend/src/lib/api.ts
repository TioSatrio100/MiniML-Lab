/**
 * api.ts - typed client for MiniML Lab FastAPI backend.
 */

export interface Provider {
  name: string
  base_url: string | null
  models: string[]
  has_key: boolean
  builtin: boolean
}

export interface SessionConfig {
  provider: string
  model_name: string
  base_url: string
  task_type: 'classification' | 'regression' | 'clustering' | 'recommendation'
  data_source: string
  ai_description: string
  n_samples: number
  n_features: number
  max_iterations: number
  target_column: string | null
}

export interface DataPreview {
  has_data: boolean
  columns?: string[]
  dtypes?: Record<string, string>
  shape?: number[]
  target?: string | null
  rows?: Record<string, unknown>[]
}

export interface SessionStatus {
  has_data: boolean
  target: string | null
  config: SessionConfig
  best_score: number
  best_model_name: string
  agent_running: boolean
  agent_trace: string[]
  iteration_results: IterationResult[]
  agent_summary: string
}

export interface IterationResult {
  status: string
  metrics?: Record<string, number>
  model_path?: string | null
  is_better?: boolean
  best_score?: number
  error?: string
}

export interface ModelInfo {
  model_name: string
  display_name: string
  saved_at: string
  metrics: Record<string, number>
}

export interface ProgressResponse {
  experiments: unknown[]
  stats: {
    total: number
    successful: number
    metric: string
    metric_label: string
    best_score: number
    improvement: number
    best_score_so_far: number
    best_model_name: string
  }
  chart: unknown
}

export interface AgentInitResult {
  ready: boolean
  error?: string
  provider?: string
  model?: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    ...init,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(detail.detail || res.statusText)
  }
  return res.json() as Promise<T>
}

export const api = {
  createSession: () => request<{ session_id: string; config: SessionConfig }>('/api/session', { method: 'POST' }),

  getConfig: (sid: string) => request<SessionConfig>(`/api/session/${sid}/config`),
  putConfig: (sid: string, patch: Partial<SessionConfig>) =>
    request<SessionConfig>(`/api/session/${sid}/config`, { method: 'PUT', body: JSON.stringify(patch) }),

  status: (sid: string) => request<SessionStatus>(`/api/session/${sid}/status`),

  generateSynthetic: (sid: string, task_type: string, n_samples: number, n_features: number) =>
    request<{ preview: DataPreview }>(`/api/session/${sid}/data/synthetic`, {
      method: 'POST',
      body: JSON.stringify({ task_type, n_samples, n_features }),
    }),

  uploadCsv: async (sid: string, file: File, target_column?: string | null) => {
    const form = new FormData()
    form.append('file', file)
    const qs = target_column ? `?target_column=${encodeURIComponent(target_column)}` : ''
    const res = await fetch(`/api/session/${sid}/data/csv${qs}`, { method: 'POST', body: form })
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText)
    return res.json() as Promise<{ preview: DataPreview }>
  },

  preview: (sid: string) => request<DataPreview>(`/api/session/${sid}/data/preview`),

  providers: () => request<Provider[]>('/api/providers'),
  addProvider: (body: { name: string; base_url: string; api_key: string; models: string[] }) =>
    request<Provider>('/api/providers', { method: 'POST', body: JSON.stringify(body) }),
  updateProvider: (name: string, body: { base_url?: string; api_key?: string }) =>
    request<Provider>(`/api/providers/${encodeURIComponent(name)}`, { method: 'PATCH', body: JSON.stringify(body) }),
  addModel: (name: string, model: string) =>
    request<{ name: string; models: string[] }>(`/api/providers/${encodeURIComponent(name)}/models`, {
      method: 'POST',
      body: JSON.stringify({ model }),
    }),
  removeProvider: (name: string) =>
    request<{ removed: string }>(`/api/providers/${encodeURIComponent(name)}`, { method: 'DELETE' }),
  discovery: (name: string) =>
    request<{ name: string; models: string[] }>(`/api/providers/${encodeURIComponent(name)}/discovery`, { method: 'POST' }),

  models: () => request<ModelInfo[]>('/api/models'),
  bestModel: (task: string) => request<ModelInfo>(`/api/models/best?task=${task}`),
  modelCode: (name: string) => request<{ model_name: string; code: string }>(`/api/models/${encodeURIComponent(name)}/code`),

  progress: (sid: string) => request<ProgressResponse>(`/api/session/${sid}/progress`),

  agentInit: (sid: string) => request<AgentInitResult>(`/api/session/${sid}/agent/init`, { method: 'POST' }),
  agentRun: (sid: string) => request<{ job_id: string }>(`/api/session/${sid}/agent/run`, { method: 'POST' }),
  agentCancel: (sid: string, job_id: string) =>
    request<{ cancelled: boolean }>(`/api/session/${sid}/agent/cancel?job_id=${job_id}`, { method: 'POST' }),
  agentStreamUrl: (sid: string, job_id: string) => `/api/session/${sid}/agent/stream/${job_id}`,
}

export type AgentEventType =
  | 'message'
  | 'tool_call'
  | 'tool_result'
  | 'progress'
  | 'trace'
  | 'iteration'
  | 'done'
  | 'error'

export interface AgentEvent {
  event: AgentEventType
  data: Record<string, unknown>
}

/**
 * Consume agent SSE stream via fetch (EventSource can't do custom event names
 * without listener-per-type; fetch reader gives full control).
 */
export async function streamAgent(
  url: string,
  onEvent: (e: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(url, { headers: { Accept: 'text/event-stream' }, signal })
  if (!res.ok || !res.body) throw new Error(`Stream failed: ${res.status}`)
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() ?? ''
    for (const chunk of chunks) {
      let event = ''
      let data = ''
      for (const line of chunk.split('\n')) {
        if (line.startsWith('event: ')) event = line.slice(7)
        else if (line.startsWith('data: ')) data += line.slice(6)
      }
      if (event && data) {
        try {
          onEvent({ event: event as AgentEventType, data: JSON.parse(data) })
        } catch {
          /* skip malformed */
        }
      }
    }
  }
}
