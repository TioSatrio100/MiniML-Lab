/**
 * store.ts - zustand app state: session, config, agent trace, iterations.
 */
import { create } from 'zustand'
import { api, type IterationResult, type Provider, type SessionConfig, type SessionStatus } from './api'

interface AppState {
  sessionId: string | null
  config: SessionConfig | null
  providers: Provider[]

  running: boolean
  trace: string[]
  iterations: IterationResult[]
  summary: string
  bestScore: number
  bestModelName: string
  error: string | null
  modelsVersion: number

  init: () => Promise<void>
  setConfig: (patch: Partial<SessionConfig>) => Promise<void>
  refreshProviders: () => Promise<void>
  applyStatus: (s: SessionStatus) => void
  pushTrace: (line: string) => void
  resetAgent: () => void
  bumpModels: () => void
}

export const useStore = create<AppState>((set, get) => ({
  sessionId: null,
  config: null,
  providers: [],

  running: false,
  trace: [],
  iterations: [],
  summary: '',
  bestScore: 0,
  bestModelName: 'None',
  error: null,
  modelsVersion: 0,

  init: async () => {
    if (get().sessionId) return
    const { session_id, config } = await api.createSession()
    const providers = await api.providers()
    set({ sessionId: session_id, config, providers })
    // rehydrate mid-run state (page refresh during agent run)
    try {
      const status = await api.status(session_id)
      get().applyStatus(status)
    } catch {
      /* status unavailable — fresh session is fine */
    }
  },

  setConfig: async (patch) => {
    const sid = get().sessionId
    if (!sid) return
    const config = await api.putConfig(sid, patch)
    set({ config })
  },

  refreshProviders: async () => set({ providers: await api.providers() }),

  applyStatus: (s) =>
    set({
      config: s.config,
      running: s.agent_running,
      trace: s.agent_trace,
      iterations: s.iteration_results,
      summary: s.agent_summary,
      bestScore: s.best_score,
      bestModelName: s.best_model_name,
    }),

  pushTrace: (line) => set((st) => ({ trace: [...st.trace, line] })),

  resetAgent: () => set({ trace: [], iterations: [], summary: '', error: null, running: false }),

  bumpModels: () => set((st) => ({ modelsVersion: st.modelsVersion + 1 })),
}))
