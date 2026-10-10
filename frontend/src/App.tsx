import { useEffect } from 'react'
import { ErrorBoundary } from './components/ErrorBoundary'
import { Sidebar } from './components/Sidebar'
import { Dashboard } from './pages/Dashboard'
import { SubmitTicket } from './pages/SubmitTicket'
import { AgentSearch } from './pages/AgentSearch'
import { TrendingIncidents } from './pages/TrendingIncidents'
import { EscalationQueue } from './pages/EscalationQueue'
import { Conversations } from './pages/Conversations'
import { KbPerformance } from './pages/KbPerformance'
import { DemoControls } from './pages/DemoControls'
import { Login } from './pages/Login'
import { Integrations } from './pages/Integrations'
import { useStore } from './store/useStore'
import { api, authToken } from './services/api'
import { useTawkTo } from './hooks/useTawkTo'

const PAGES: Record<string, React.ComponentType> = {
  dashboard:     Dashboard,
  submit:        SubmitTicket,
  agent:         AgentSearch,
  trending:      TrendingIncidents,
  escalation:    EscalationQueue,
  conversations: Conversations,
  kb:            KbPerformance,
  demo:          DemoControls,
  integrations:  Integrations,
  login:         Login,
}

// Pages that show customer data or settings — agents only
const STAFF_ONLY = new Set(['escalation', 'conversations', 'integrations'])

export default function App() {
  const { activePage, setApiConnected, user, setUser, authRequired, setAuthRequired } = useStore()

  // Initialize Tawk.to (hidden by default, shown only on escalation)
  useTawkTo()

  useEffect(() => {
    api.healthCheck()
      .then(() => setApiConnected(true))
      .catch(() => setApiConnected(false))
  }, [setApiConnected])

  // Does the server require login, and is the saved token still good?
  useEffect(() => {
    api.authStatus().then(s => setAuthRequired(s.auth_required)).catch(() => {})
    if (authToken.get()) {
      api.me().then(setUser).catch(() => authToken.clear())
    }
    const onLogout = () => setUser(null)
    window.addEventListener('copilot:logout', onLogout)
    return () => window.removeEventListener('copilot:logout', onLogout)
  }, [setAuthRequired, setUser])

  const locked = STAFF_ONLY.has(activePage) && authRequired && !user
  const Page = locked ? Login : (PAGES[activePage] || Dashboard)

  return (
    <ErrorBoundary>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar />
        <main style={{ flex: 1, overflowY: 'auto', maxHeight: '100vh' }}>
          <Page />
        </main>
      </div>
    </ErrorBoundary>
  )
}
