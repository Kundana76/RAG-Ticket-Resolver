import axios from 'axios'

const BASE = '/api'

const client = axios.create({ baseURL: BASE, timeout: 15000 })

// ── Auth token (kept in localStorage; every request sends it when present) ──
const TOKEN_KEY = 'copilot_token'
export const authToken = {
  get: (): string | null => { try { return localStorage.getItem(TOKEN_KEY) } catch { return null } },
  set: (t: string) => { try { localStorage.setItem(TOKEN_KEY, t) } catch { /* private mode */ } },
  clear: () => { try { localStorage.removeItem(TOKEN_KEY) } catch { /* private mode */ } },
}

client.interceptors.request.use(cfg => {
  const t = authToken.get()
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

// An expired or invalid token logs the user out everywhere in the UI.
client.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401 && authToken.get()) {
      authToken.clear()
      window.dispatchEvent(new Event('copilot:logout'))
    }
    return Promise.reject(err)
  },
)

export const errorMessage = (e: any, fallback = 'Something went wrong'): string => {
  const d = e?.response?.data?.detail
  if (typeof d === 'string') return d
  if (d?.message) return d.message
  return e?.response ? fallback : 'Cannot reach the API — is the backend running?'
}

export interface TicketInput {
  ticket_id?: string
  ticket_text: string
  category?: string
  confidence?: number
}

export interface ProcessResult {
  ticket_id: string
  category: string
  confidence: number
  action: 'auto_resolved' | 'draft_response' | 'escalated'
  resolution: {
    action: string
    confidence_tier: string
    resolution?: string
    draft?: string
    source_article?: string
    summary?: { issue_summary: string; probable_root_cause: string; priority: string; attempted_fixes: string }
    recommendations?: any[]
    timestamp: string
    confidence_score: number
  }
  recommendations: Array<{ rank: number; article_title: string; score: number }>
  timestamp: string
  latency_ms: number
}

export interface LiveMetrics {
  total_tickets_today: number
  auto_resolved: number
  escalated: number
  draft_responses: number
  active_users: number
  auto_resolution_rate: number
  escalation_rate: number
  categories: Record<string, number>
}

export interface TrendingItem {
  category: string
  score: number
  is_spike: boolean
  window: string
}

export interface ActivityItem {
  id: string
  ticket_id: string
  category: string
  action: string
  confidence: number
  timestamp: string
}

export interface EscalationItem {
  ticket_id: string
  ticket_text: string
  category: string
  confidence_score: number
  issue_summary: string
  attempted_fixes: string
  probable_root_cause: string
  priority: 'high' | 'medium' | 'low'
  recommended_articles: Array<{ title: string; score: number }>
  status: string
  created_at: string
}

export interface User { username: string; role: 'agent' | 'admin' }
export interface AuthStatus { auth_required: boolean; has_users: boolean }

export interface FeedbackResult {
  article_title: string
  helpful_votes: number
  unhelpful_votes: number
  adjustment: number
  changed: boolean
}
export interface FeedbackStats {
  total_votes: number
  helpful_rate: number | null
  articles: Array<{ article_title: string; helpful: number; unhelpful: number; helpful_rate: number; adjustment: number }>
  recent: Array<{ ticket_id: string; article_title: string; helpful: boolean; comment: string; timestamp: string }>
}

export interface IntegrationStatus {
  email: {
    configured: boolean
    auto_reply: boolean
    poll_seconds: number
    last_poll: null | { fetched?: number; processed?: number; skipped?: number; errors?: string[]; at?: string }
  }
  webhook: { enabled: boolean; path: string }
  slack: { enabled: boolean }
}

export const api = {
  processTicket: (data: TicketInput) =>
    client.post<ProcessResult>('/copilot/process', data).then(r => r.data),

  agentSearch: (message: string, session_id?: string) =>
    client.post('/agent/search', { message, session_id }).then(r => r.data),

  getLiveMetrics: () =>
    client.get<LiveMetrics>('/analytics/live').then(r => r.data),

  getDashboard: () =>
    client.get('/analytics/dashboard').then(r => r.data),

  getHourlyTrend: (hours = 12) =>
    client.get(`/analytics/trend?hours=${hours}`).then(r => r.data),

  getActivityFeed: (count = 20) =>
    client.get<ActivityItem[]>(`/analytics/activity-feed?count=${count}`).then(r => r.data),

  getKbPerformance: () =>
    client.get('/analytics/kb-performance').then(r => r.data),

  getTrending: (window = '1h') =>
    client.get(`/trending?window=${window}`).then(r => r.data),

  getEscalationQueue: () =>
    client.get('/escalation/queue').then(r => r.data),

  claimEscalation: () =>
    client.post('/escalation/claim', {}).then(r => r.data),

  resolveEscalation: (ticket_id: string, resolution_note: string) =>
    client.post('/escalation/resolve', { ticket_id, resolution_note }).then(r => r.data),

  // auth
  authStatus: () => client.get<AuthStatus>('/auth/status').then(r => r.data),
  login: (username: string, password: string) =>
    client.post<{ token: string; user: User }>('/auth/login', { username, password }).then(r => r.data),
  register: (username: string, password: string, role?: string) =>
    client.post<{ token?: string; user: User }>('/auth/register', { username, password, role }).then(r => r.data),
  me: () => client.get<User>('/auth/me').then(r => r.data),

  // feedback
  sendFeedback: (ticket_id: string, article_title: string, helpful: boolean) =>
    client.post<FeedbackResult>('/feedback', { ticket_id, article_title, helpful }).then(r => r.data),
  getFeedbackStats: () => client.get<FeedbackStats>('/feedback/stats').then(r => r.data),

  // integrations
  getIntegrations: () => client.get<IntegrationStatus>('/integrations/status').then(r => r.data),
  pollEmail: () => client.post('/integrations/email/poll').then(r => r.data),

  getRecentConversations: () =>
    client.get('/conversations/recent').then(r => r.data),

  getConversation: (id: string) =>
    client.get(`/conversation/${id}`).then(r => r.data),

  getSampleTickets: () =>
    client.get('/demo/sample-tickets').then(r => r.data),

  batchProcess: (tickets: any[]) =>
    client.post('/demo/batch', { tickets }).then(r => r.data),

  resetDemo: () =>
    client.post('/demo/reset', {}).then(r => r.data),

  healthCheck: () =>
    client.get('/').then(r => r.data),
}
