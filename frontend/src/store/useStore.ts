import { create } from 'zustand'
import type { LiveMetrics, ActivityItem, TrendingItem, EscalationItem, ProcessResult, User } from '../services/api'

interface AppState {
  // Connection
  apiConnected: boolean
  setApiConnected: (v: boolean) => void

  // Metrics
  metrics: LiveMetrics | null
  setMetrics: (m: LiveMetrics) => void

  // Activity feed
  activityFeed: ActivityItem[]
  setActivityFeed: (feed: ActivityItem[]) => void
  prependActivity: (item: ActivityItem) => void

  // Trending
  trending: TrendingItem[]
  setTrending: (t: TrendingItem[]) => void

  // Escalation queue
  escalationQueue: EscalationItem[]
  setEscalationQueue: (q: EscalationItem[]) => void

  // Escalation queue length (for sidebar badge)
  escalationQueueLength: number
  setEscalationQueueLength: (n: number) => void

  // Last processed ticket
  lastResult: ProcessResult | null
  setLastResult: (r: ProcessResult | null) => void

  // Signed-in agent (null when signed out) and whether the server enforces login
  user: User | null
  setUser: (u: User | null) => void
  authRequired: boolean
  setAuthRequired: (v: boolean) => void

  // Active page
  activePage: string
  setActivePage: (p: string) => void

  // Hourly trend
  hourlyTrend: any[]
  setHourlyTrend: (t: any[]) => void
}

export const useStore = create<AppState>((set) => ({
  apiConnected: false,
  setApiConnected: (v) => set({ apiConnected: v }),

  metrics: null,
  setMetrics: (m) => set({ metrics: m }),

  activityFeed: [],
  setActivityFeed: (feed) => set({ activityFeed: feed }),
  prependActivity: (item) =>
    set((s) => ({ activityFeed: [item, ...s.activityFeed].slice(0, 50) })),

  trending: [],
  setTrending: (t) => set({ trending: t }),

  escalationQueue: [],
  setEscalationQueue: (q) => set({ escalationQueue: q }),

  escalationQueueLength: 0,
  setEscalationQueueLength: (n) => set({ escalationQueueLength: n }),

  lastResult: null,
  setLastResult: (r) => set({ lastResult: r }),

  user: null,
  setUser: (u) => set({ user: u }),
  authRequired: true,
  setAuthRequired: (v) => set({ authRequired: v }),

  activePage: 'dashboard',
  setActivePage: (p) => set({ activePage: p }),

  hourlyTrend: [],
  setHourlyTrend: (t) => set({ hourlyTrend: t }),
}))
