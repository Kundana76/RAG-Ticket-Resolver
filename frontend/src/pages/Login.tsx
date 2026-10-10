import { useEffect, useState } from 'react'
import { api, authToken, errorMessage } from '../services/api'
import { useStore } from '../store/useStore'

const label: React.CSSProperties = { fontSize: '0.75rem', color: '#9575cd', display: 'block', marginBottom: 6 }

export function Login() {
  const { user, setUser, setActivePage } = useStore()
  const [hasUsers, setHasUsers] = useState<boolean | null>(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  // admin: add a teammate
  const [newName, setNewName] = useState('')
  const [newPass, setNewPass] = useState('')
  const [newRole, setNewRole] = useState('agent')
  const [added, setAdded] = useState('')

  useEffect(() => {
    api.authStatus().then(s => setHasUsers(s.has_users)).catch(() => setHasUsers(true))
  }, [])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const r = hasUsers
        ? await api.login(username, password)
        : await api.register(username, password)
      if (!r.token) throw new Error('No token returned')
      authToken.set(r.token)
      setUser(r.user)
      setPassword('')
      setActivePage('escalation')
    } catch (err) {
      setError(errorMessage(err, 'Could not sign in'))
    } finally {
      setBusy(false)
    }
  }

  const addUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(''); setAdded('')
    try {
      const r = await api.register(newName, newPass, newRole)
      setAdded(`Created ${r.user.username} (${r.user.role})`)
      setNewName(''); setNewPass('')
    } catch (err) {
      setError(errorMessage(err, 'Could not create the account'))
    }
  }

  const logout = () => { authToken.clear(); setUser(null) }

  if (user) {
    return (
      <div style={{ padding: 28, maxWidth: 520 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ede7f6', marginBottom: 4 }}>Account</h1>
        <p style={{ color: '#9575cd', marginBottom: 20, fontSize: '0.9rem' }}>
          Signed in as <b style={{ color: '#ede7f6' }}>{user.username}</b> ({user.role})
        </p>
        <button className="btn-primary" onClick={logout}>Sign out</button>

        {user.role === 'admin' && (
          <form onSubmit={addUser} className="glass-card" style={{ padding: 20, marginTop: 28 }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ede7f6', marginBottom: 14 }}>Add a teammate</div>
            <label style={label} htmlFor="nn">Username</label>
            <input id="nn" className="input-field" value={newName} onChange={e => setNewName(e.target.value)}
              autoComplete="off" required />
            <label style={{ ...label, marginTop: 12 }} htmlFor="np">Temporary password (8+ characters)</label>
            <input id="np" className="input-field" type="password" value={newPass}
              onChange={e => setNewPass(e.target.value)} autoComplete="new-password" required minLength={8} />
            <label style={{ ...label, marginTop: 12 }} htmlFor="nr">Role</label>
            <select id="nr" className="input-field" value={newRole} onChange={e => setNewRole(e.target.value)}>
              <option value="agent">Agent — works the escalation queue</option>
              <option value="admin">Admin — also resets data and adds people</option>
            </select>
            <button className="btn-primary" style={{ marginTop: 16 }} type="submit">Create account</button>
            {added && <div style={{ marginTop: 12, fontSize: '0.8rem', color: '#00e676' }}>{added}</div>}
            {error && <div style={{ marginTop: 12, fontSize: '0.8rem', color: '#ff6b6b' }}>{error}</div>}
          </form>
        )}
      </div>
    )
  }

  const creating = hasUsers === false

  return (
    <div style={{ padding: 28, maxWidth: 420 }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ede7f6', marginBottom: 4 }}>
        {creating ? 'Create the admin account' : 'Agent sign in'}
      </h1>
      <p style={{ color: '#9575cd', marginBottom: 20, fontSize: '0.9rem' }}>
        {creating
          ? 'No accounts exist yet. The first one becomes the admin; after that, only an admin can add people.'
          : 'The escalation queue, conversations and integrations are for signed-in agents.'}
      </p>
      <form onSubmit={submit} className="glass-card" style={{ padding: 20 }}>
        <label style={label} htmlFor="u">Username</label>
        <input id="u" className="input-field" value={username} onChange={e => setUsername(e.target.value)}
          autoComplete="username" required autoFocus />
        <label style={{ ...label, marginTop: 12 }} htmlFor="p">Password</label>
        <input id="p" className="input-field" type="password" value={password}
          onChange={e => setPassword(e.target.value)}
          autoComplete={creating ? 'new-password' : 'current-password'} required minLength={creating ? 8 : undefined} />
        <button className="btn-primary" style={{ marginTop: 16, width: '100%' }} type="submit"
          disabled={busy || hasUsers === null}>
          {busy ? 'Please wait…' : creating ? 'Create account' : 'Sign in'}
        </button>
        {error && <div role="alert" style={{ marginTop: 12, fontSize: '0.8rem', color: '#ff6b6b' }}>{error}</div>}
      </form>
    </div>
  )
}
