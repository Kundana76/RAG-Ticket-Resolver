import { useState } from 'react'
import { motion } from 'framer-motion'
import { Search } from 'lucide-react'
import { api } from '../services/api'
import { usePolling } from '../hooks/usePolling'
import { ActionBadge } from '../components/ActionBadge'
import { ConfidenceBar } from '../components/ConfidenceBar'

export function Conversations() {
  const [recent, setRecent] = useState<any[]>([])
  const [searchId, setSearchId] = useState('')
  const [detail, setDetail] = useState<any>(null)
  const [searching, setSearching] = useState(false)

  usePolling(async () => {
    try { setRecent(await api.getRecentConversations()) } catch {}
  }, 6000)

  const search = async () => {
    if (!searchId.trim()) return
    setSearching(true)
    try { setDetail(await api.getConversation(searchId.trim())) }
    catch { setDetail(null) }
    finally { setSearching(false) }
  }

  return (
    <div style={{ padding: 28 }}>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ede7f6', marginBottom: 4 }}>
          💬 Conversation Memory
        </h1>
        <p style={{ color: '#9575cd', marginBottom: 20, fontSize: '0.9rem' }}>
          Valkey JSON — JSON.SET / JSON.GET per ticket lifecycle
        </p>

        {/* Search */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
          <input className="input-field" placeholder="Search by ticket ID (ticket:uuid)…"
            value={searchId} onChange={e => setSearchId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()} />
          <button className="btn-primary" onClick={search} disabled={searching}
            style={{ padding: '10px 16px', flexShrink: 0, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Search size={14} /> Search
          </button>
        </div>

        {detail && (
          <div className="glass-card" style={{ padding: 20, marginBottom: 20 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginBottom: 16 }}>
              {[
                { label: 'Status', value: detail.status },
                { label: 'Category', value: detail.category },
                { label: 'Confidence', value: `${((detail.confidence_score || 0) * 100).toFixed(0)}%` },
              ].map(({ label, value }) => (
                <div key={label} style={{ padding: '10px 14px', background: 'rgba(123,47,190,0.1)', borderRadius: 8 }}>
                  <div style={{ fontSize: '0.7rem', color: '#9575cd', textTransform: 'uppercase', letterSpacing: 1 }}>{label}</div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: '#ede7f6', marginTop: 2 }}>{value || '—'}</div>
                </div>
              ))}
            </div>
            <ConfidenceBar value={detail.confidence_score || 0} />
            <div style={{ marginTop: 12, fontSize: '0.85rem', color: '#b39ddb', lineHeight: 1.6 }}>
              {detail.ticket_text}
            </div>
            {detail.turns?.length > 0 && (
              <div style={{ marginTop: 14 }}>
                <div style={{ fontSize: '0.75rem', color: '#9575cd', marginBottom: 8, fontWeight: 600 }}>TURNS</div>
                {detail.turns.map((t: any, i: number) => (
                  <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6, fontSize: '0.82rem' }}>
                    <span style={{ color: t.role === 'user' ? '#b39ddb' : '#00e676', minWidth: 60 }}>
                      {t.role === 'user' ? '👤 User' : '🤖 Agent'}
                    </span>
                    <span style={{ color: '#9575cd', minWidth: 80 }}>{t.timestamp?.slice(11, 19)}</span>
                    <span style={{ color: '#ede7f6' }}>{t.content?.slice(0, 80)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Recent table */}
        <div className="glass-card" style={{ padding: 20 }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ede7f6', marginBottom: 16 }}>
            Recent Conversations
          </h3>
          {recent.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(123,47,190,0.2)' }}>
                  {['Ticket ID', 'Category', 'Status', 'Confidence', 'Updated'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#9575cd',
                      fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: 1 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recent.map((c, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(123,47,190,0.08)',
                    cursor: 'pointer', transition: 'background 0.15s' }}
                    onClick={() => setSearchId(c.ticket_id)}
                    onMouseEnter={e => (e.currentTarget.style.background = 'rgba(123,47,190,0.08)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                    <td style={{ padding: '8px 12px' }}>
                      <code style={{ color: '#9575cd', fontSize: '0.75rem' }}>{c.ticket_id?.slice(0, 26)}…</code>
                    </td>
                    <td style={{ padding: '8px 12px', color: '#b39ddb' }}>{c.category || '—'}</td>
                    <td style={{ padding: '8px 12px' }}><ActionBadge action={c.status} /></td>
                    <td style={{ padding: '8px 12px', color: '#ede7f6' }}>
                      {((c.confidence_score || 0) * 100).toFixed(0)}%
                    </td>
                    <td style={{ padding: '8px 12px', color: '#6b5b8a' }}>{c.updated_at?.slice(0, 19)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ color: '#6b5b8a', textAlign: 'center', padding: '30px 0', fontSize: '0.85rem' }}>
              No conversations yet. Submit tickets to see them here.
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}
