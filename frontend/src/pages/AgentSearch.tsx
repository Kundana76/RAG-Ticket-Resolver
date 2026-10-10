import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, RefreshCw, Bot, User } from 'lucide-react'
import { api } from '../services/api'
import { ActionBadge } from '../components/ActionBadge'

interface Turn { role: 'user' | 'assistant'; content: string; meta?: any }

export function AgentSearch() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [sessionId, setSessionId] = useState<string | undefined>()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns])

  const send = async () => {
    if (!input.trim() || loading) return
    const msg = input.trim()
    setInput('')
    setTurns(t => [...t, { role: 'user', content: msg }])
    setLoading(true)
    try {
      const r = await api.agentSearch(msg, sessionId)
      setSessionId(r.session_id)
      const resp = r.response + (r.follow_up ? `\n\n*${r.follow_up}*` : '')
      setTurns(t => [...t, { role: 'assistant', content: resp, meta: r }])
    } catch {
      setTurns(t => [...t, { role: 'assistant', content: 'Agent unavailable. Is the API running?' }])
    } finally {
      setLoading(false)
    }
  }

  const reset = () => { setTurns([]); setSessionId(undefined) }

  return (
    <div style={{ padding: 28, maxWidth: 800, display: 'flex', flexDirection: 'column', height: 'calc(100vh - 40px)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ede7f6', marginBottom: 4 }}>
            🤖 Agentic Search
          </h1>
          <p style={{ color: '#9575cd', fontSize: '0.9rem' }}>
            Natural language support — conversation memory in Valkey JSON
          </p>
        </div>
        <button onClick={reset} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '8px 14px', background: 'rgba(123,47,190,0.15)',
          border: '1px solid rgba(123,47,190,0.3)', borderRadius: 8,
          color: '#9575cd', cursor: 'pointer', fontSize: '0.82rem',
        }}>
          <RefreshCw size={14} /> New Session
        </button>
      </div>

      {/* Chat area */}
      <div className="glass-card" style={{ flex: 1, overflowY: 'auto', padding: 20, marginBottom: 16 }}>
        {turns.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: '#6b5b8a' }}>
            <Bot size={40} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
            <div style={{ fontSize: '0.9rem' }}>Describe your issue in natural language.</div>
            <div style={{ fontSize: '0.8rem', marginTop: 4 }}>The AI agent will classify, search KB, and resolve or escalate.</div>
          </div>
        )}
        <AnimatePresence>
          {turns.map((turn, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                display: 'flex', gap: 12, marginBottom: 16,
                flexDirection: turn.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              <div style={{
                width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                background: turn.role === 'user' ? 'rgba(123,47,190,0.3)' : 'rgba(0,230,118,0.15)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {turn.role === 'user' ? <User size={16} color="#b39ddb" /> : <Bot size={16} color="#00e676" />}
              </div>
              <div style={{ maxWidth: '80%' }}>
                <div style={{
                  padding: '10px 14px', borderRadius: 10,
                  background: turn.role === 'user' ? 'rgba(123,47,190,0.2)' : 'rgba(30,16,53,0.8)',
                  border: `1px solid ${turn.role === 'user' ? 'rgba(123,47,190,0.3)' : 'rgba(0,230,118,0.15)'}`,
                  color: '#ede7f6', fontSize: '0.88rem', lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                }}>
                  {turn.content}
                </div>
                {turn.meta?.results?.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    {turn.meta.results.slice(0, 3).map((r: any, j: number) => (
                      <div key={j} style={{
                        padding: '6px 10px', marginBottom: 4,
                        background: 'rgba(123,47,190,0.08)',
                        border: '1px solid rgba(123,47,190,0.2)',
                        borderRadius: 6, fontSize: '0.78rem', color: '#b39ddb',
                      }}>
                        📄 {r.article_title} — {(r.score * 100).toFixed(0)}%
                      </div>
                    ))}
                  </div>
                )}
                {turn.meta?.action && (
                  <div style={{ marginTop: 6 }}>
                    <ActionBadge action={turn.meta.action} />
                    {sessionId && (
                      <span style={{ marginLeft: 8, fontSize: '0.7rem', color: '#6b5b8a' }}>
                        Session: {sessionId.slice(0, 24)}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {loading && (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%',
              background: 'rgba(0,230,118,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={16} color="#00e676" />
            </div>
            <div style={{ padding: '10px 14px', background: 'rgba(30,16,53,0.8)',
              border: '1px solid rgba(0,230,118,0.15)', borderRadius: 10 }}>
              <Loader2 size={16} color="#9575cd" className="animate-spin" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: 10 }}>
        <input
          className="input-field"
          placeholder="Describe your issue in natural language…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          disabled={loading}
        />
        <button className="btn-primary" onClick={send} disabled={loading || !input.trim()}
          style={{ padding: '10px 16px', flexShrink: 0 }}>
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </div>
    </div>
  )
}
