import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertOctagon, ChevronDown, ChevronUp, UserCheck, Loader2 } from 'lucide-react'
import { api, errorMessage } from '../services/api'
import { useStore } from '../store/useStore'
import { usePolling } from '../hooks/usePolling'
import { ConfidenceBar } from '../components/ConfidenceBar'

export function EscalationQueue() {
  const [queue, setQueue] = useState<any[]>([])
  const [stats, setStats] = useState({ pending: 0 })
  const [expanded, setExpanded] = useState<string | null>(null)
  const { user } = useStore()
  const [claiming, setClaiming] = useState(false)
  const [claimResult, setClaimResult] = useState<any>(null)
  const [claimError, setClaimError] = useState('')
  const [note, setNote] = useState('')
  const [resolving, setResolving] = useState(false)
  const [resolved, setResolved] = useState('')

  const refresh = async () => {
    try {
      const d = await api.getEscalationQueue()
      setQueue(d.queue || [])
      setStats(d.stats || { pending: 0 })
    } catch {}
  }

  usePolling(refresh, 4000)

  const claim = async () => {
    setClaiming(true); setClaimError(''); setResolved('')
    try {
      const r = await api.claimEscalation()
      setClaimResult(r)
      setNote('')
      refresh()
    } catch (e) {
      setClaimResult(null)
      setClaimError(errorMessage(e, 'Could not claim a ticket'))
    } finally {
      setClaiming(false)
    }
  }

  const resolve = async () => {
    if (!claimResult || !note.trim()) return
    setResolving(true); setClaimError('')
    try {
      await api.resolveEscalation(claimResult.ticket_id, note.trim())
      setResolved(claimResult.ticket_id)
      setClaimResult(null)
      setNote('')
    } catch (e) {
      setClaimError(errorMessage(e, 'Could not save the resolution'))
    } finally {
      setResolving(false)
    }
  }

  const priorityColor = (p: string) =>
    p === 'high' ? '#ff1744' : p === 'medium' ? '#ffd600' : '#00e676'

  return (
    <div style={{ padding: 28 }}>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ede7f6', marginBottom: 4 }}>
          🚨 Escalation Queue
        </h1>
        <p style={{ color: '#9575cd', marginBottom: 20, fontSize: '0.9rem' }}>
          Valkey List (LPUSH / RPOP) — FIFO escalation queue
        </p>

        {/* Stats + claim */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 24, alignItems: 'flex-start' }}>
          <div className="glass-card" style={{ padding: 20, minWidth: 160 }}>
            <div style={{ fontSize: '0.75rem', color: '#9575cd', textTransform: 'uppercase', letterSpacing: 1 }}>
              Pending
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: stats.pending > 0 ? '#ff1744' : '#00e676' }}>
              {stats.pending}
            </div>
          </div>
          <div className="glass-card" style={{ padding: 20, flex: 1 }}>
            <div style={{ fontSize: '0.8rem', color: '#9575cd', marginBottom: 10 }}>CLAIM NEXT ESCALATION</div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <button className="btn-primary" onClick={claim} disabled={claiming || stats.pending === 0}
                style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                {claiming ? <Loader2 size={14} className="animate-spin" /> : <UserCheck size={14} />}
                Claim oldest ticket
              </button>
              {user && (
                <span style={{ fontSize: '0.78rem', color: '#9575cd' }}>
                  as <b style={{ color: '#ede7f6' }}>{user.username}</b>
                </span>
              )}
            </div>
            {claimError && (
              <div role="alert" style={{ marginTop: 10, fontSize: '0.8rem', color: '#ff6b6b' }}>{claimError}</div>
            )}
            {resolved && (
              <div style={{ marginTop: 10, padding: '8px 12px', background: 'rgba(0,230,118,0.1)',
                border: '1px solid rgba(0,230,118,0.2)', borderRadius: 6, fontSize: '0.8rem', color: '#00e676' }}>
                Resolved {resolved.slice(0, 28)}
              </div>
            )}
            {claimResult && (
              <div style={{ marginTop: 12, padding: '12px 14px', background: 'rgba(123,47,190,0.12)',
                border: '1px solid rgba(123,47,190,0.3)', borderRadius: 8 }}>
                <div style={{ fontSize: '0.78rem', color: '#9575cd', marginBottom: 6 }}>
                  You claimed <code>{claimResult.ticket_id?.slice(0, 28)}</code>
                </div>
                <div style={{ fontSize: '0.85rem', color: '#ede7f6', lineHeight: 1.5, marginBottom: 10 }}>
                  {claimResult.ticket_text}
                </div>
                <textarea className="input-field" rows={3} value={note} onChange={e => setNote(e.target.value)}
                  placeholder="What did you do to fix it?" style={{ resize: 'vertical' }} />
                <button className="btn-primary" style={{ marginTop: 10 }} onClick={resolve}
                  disabled={resolving || !note.trim()}>
                  {resolving ? 'Saving…' : 'Mark resolved'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Queue */}
        {queue.length === 0 ? (
          <div className="glass-card" style={{ padding: 40, textAlign: 'center' }}>
            <AlertOctagon size={40} style={{ margin: '0 auto 12px', color: '#00e676', opacity: 0.5 }} />
            <div style={{ color: '#00e676', fontWeight: 700 }}>Queue Empty — All Clear!</div>
            <div style={{ color: '#6b5b8a', fontSize: '0.85rem', marginTop: 4 }}>
              No tickets require human intervention.
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <AnimatePresence>
              {queue.map((item, i) => (
                <motion.div
                  key={item.ticket_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="glass-card"
                  style={{ overflow: 'hidden', borderLeft: `4px solid ${priorityColor(item.priority)}` }}
                >
                  <div
                    style={{ padding: '14px 18px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12 }}
                    onClick={() => setExpanded(expanded === item.ticket_id ? null : item.ticket_id)}
                  >
                    <span style={{ fontSize: '1rem' }}>
                      {item.priority === 'high' ? '🔴' : item.priority === 'medium' ? '🟡' : '🟢'}
                    </span>
                    <code style={{ fontSize: '0.75rem', color: '#9575cd', minWidth: 180 }}>
                      {item.ticket_id?.slice(0, 26)}…
                    </code>
                    <span style={{ flex: 1, fontSize: '0.85rem', color: '#ede7f6' }}>
                      {item.issue_summary?.slice(0, 60)}…
                    </span>
                    <span style={{ fontSize: '0.75rem', color: priorityColor(item.priority),
                      fontWeight: 700, textTransform: 'uppercase', minWidth: 60 }}>
                      {item.priority}
                    </span>
                    {expanded === item.ticket_id ? <ChevronUp size={16} color="#9575cd" /> : <ChevronDown size={16} color="#9575cd" />}
                  </div>

                  <AnimatePresence>
                    {expanded === item.ticket_id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        style={{ overflow: 'hidden' }}
                      >
                        <div style={{ padding: '0 18px 18px', borderTop: '1px solid rgba(123,47,190,0.2)' }}>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
                            <div>
                              <div style={{ fontSize: '0.75rem', color: '#9575cd', marginBottom: 6 }}>TICKET TEXT</div>
                              <div style={{ fontSize: '0.85rem', color: '#ede7f6', lineHeight: 1.5 }}>
                                {item.ticket_text}
                              </div>
                              <div style={{ marginTop: 12 }}>
                                <ConfidenceBar value={item.confidence_score || 0} />
                              </div>
                            </div>
                            <div>
                              <div style={{ fontSize: '0.75rem', color: '#9575cd', marginBottom: 6 }}>ROOT CAUSE</div>
                              <div style={{ fontSize: '0.85rem', color: '#ff6b6b', marginBottom: 10 }}>
                                {item.probable_root_cause}
                              </div>
                              <div style={{ fontSize: '0.75rem', color: '#9575cd', marginBottom: 6 }}>ATTEMPTED FIXES</div>
                              <div style={{ fontSize: '0.82rem', color: '#b39ddb' }}>{item.attempted_fixes}</div>
                              {item.recommended_articles?.length > 0 && (
                                <>
                                  <div style={{ fontSize: '0.75rem', color: '#9575cd', marginTop: 10, marginBottom: 6 }}>
                                    KB ARTICLES
                                  </div>
                                  {item.recommended_articles.map((a: any, j: number) => (
                                    <div key={j} style={{ fontSize: '0.78rem', color: '#b39ddb', marginBottom: 3 }}>
                                      📄 {a.title} ({(a.score * 100).toFixed(0)}%)
                                    </div>
                                  ))}
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </motion.div>
    </div>
  )
}
