/**
 * runAgent.ts - kick off agent run, consume SSE, update store.
 */
import { api, streamAgent, type AgentEvent } from './api'
import { useStore } from './store'

let abort: AbortController | null = null
let currentJob: { sid: string; jobId: string } | null = null

export function cancelRun() {
  const st = useStore.getState()
  // tell server to stop the agent first — aborting fetch alone leaves it running
  if (currentJob) {
    api.agentCancel(currentJob.sid, currentJob.jobId).catch(() => {})
  }
  abort?.abort()
  abort = null
  currentJob = null
  st.resetAgent()
  void api.progress(st.sessionId ?? '').catch(() => {})
}

export async function runAgent(): Promise<void> {
  const st = useStore.getState()
  const sid = st.sessionId
  if (!sid || st.running) return

  st.resetAgent()
  st.pushTrace('⚡ initializing agent…')

  const init = await api.agentInit(sid)
  if (!init.ready) {
    useStore.setState({ error: init.error ?? 'Agent init failed', running: false })
    return
  }
  st.pushTrace(`⚡ provider=${init.provider} model=${init.model}`)

  let job_id: string
  try {
    ;({ job_id } = await api.agentRun(sid))
  } catch (e) {
    // 400 no dataset, 409 already running, etc. — surface, don't swallow
    useStore.setState({ error: String((e as Error).message ?? e), running: false })
    return
  }
  currentJob = { sid, jobId: job_id }
  useStore.setState({ running: true })
  abort = new AbortController()

  const handleEvent = (e: AgentEvent) => {
    const s = useStore.getState()
    switch (e.event) {
      case 'trace':
        s.pushTrace(String(e.data.line))
        break
      case 'iteration': {
        const iter = e.data as { status?: string; is_better?: boolean; best_score?: number }
        const next = [...s.iterations, e.data as never]
        useStore.setState({
          iterations: next,
          bestScore: iter.is_better && typeof iter.best_score === 'number' ? iter.best_score : s.bestScore,
          error: iter.status === 'failed' ? String((e.data as { error?: string }).error ?? '') : s.error,
        })
        break
      }
      case 'done': {
        useStore.setState({
          running: false,
          summary: String(e.data.summary ?? ''),
          bestScore: Number(e.data.best_score ?? s.bestScore),
          bestModelName: String(e.data.best_model_name ?? s.bestModelName),
        })
        s.bumpModels()
        break
      }
      case 'error':
        useStore.setState({ error: String(e.data.message ?? 'stream error') })
        break
      default:
        break
    }
  }

  try {
    await streamAgent(api.agentStreamUrl(sid, job_id), handleEvent, abort.signal)
  } catch (e) {
    if ((e as Error).name !== 'AbortError') {
      useStore.setState({ error: String((e as Error).message ?? e), running: false })
    }
  } finally {
    useStore.setState({ running: false })
    abort = null
    currentJob = null
    useStore.getState().bumpModels()
  }
}
