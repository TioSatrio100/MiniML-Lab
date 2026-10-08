/**
 * store.ts - zustand app state: session, config, agent trace, iterations.
 */
import { create } from 'zustand'
import { api, type DataPreview, type IterationResult, type Provider, type SessionConfig, type SessionStatus } from './api'

type TabId = 'benchmark' | 'models' | 'sandbox'

interface AppState {
  sessionId: string | null
  config: SessionConfig | null
  providers: Provider[]
  preview: DataPreview | null
  activeTab: TabId

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
  setTab: (t: TabId) => void
  applyStatus: (s: SessionStatus) => void
  pushTrace: (line: string) => void
  resetAgent: () => void
  bumpModels: () => void
}

export const useStore = create<AppState>((set, get) => ({
  sessionId: null,
  config: null,
  providers: [],
  preview: null,
  activeTab: 'benchmark',

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
  },

  setConfig: async (patch) => {
    const sid = get().sessionId
    if (!sid) return
    const config = await api.putConfig(sid, patch)
    set({ config })
  },

  refreshProviders: async () => set({ providers: await api.providers() }),

  setTab: (t) => set({ activeTab: t }),

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
