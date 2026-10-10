import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, ChevronRight, Headphones } from 'lucide-react'
import { api } from '../services/api'
import { useStore } from '../store/useStore'
import { ActionBadge } from '../components/ActionBadge'
import { ConfidenceBar } from '../components/ConfidenceBar'
import { EscalationModal } from '../components/EscalationModal'
import { FeedbackButtons } from '../components/FeedbackButtons'

const CATEGORIES = ['', 'payment', 'login', 'refund', 'delivery', 'technical',
  'payment_failure', 'login_issue', 'api_error', 'delivery_complaint',
  'billing_dispute', 'account_locked', 'refund_request', 'service_outage']

const SAMPLES = [
  'Payment failed after checkout, money deducted but order not placed',
  'Unable to login, password reset email not arriving',
  'Refund not received after 10 days of cancellation',
  'Order delayed by 2 weeks, no tracking update',
  'API returning 500 errors on all endpoints since morning',
  'Account locked after too many login attempts',
]

export function SubmitTicket() {
  const { setLastResult } = useStore()
  const [text, setText] = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')
  const [showEscalation, setShowEscalation] = useState(false)

  const submit = async () => {
    if (!text.trim()) return
    setLoading(true); setError(''); setResult(null); setShowEscalation(false)
    try {
      const r = await api.processTicket({ ticket_text: text, category: category || undefined })
      setResult(r)
      setLastResult(r)
      // Scroll to result
      setTimeout(() => {
        document.getElementById('ticket-result')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail) || 'Failed to process ticket. Is the API running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 28, maxWidth: 900 }}>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ede7f6', marginBottom: 4 }}>
          🎫 Submit Ticket
        </h1>
        <p style={{ color: '#9575cd', marginBottom: 24, fontSize: '0.9rem' }}>
          Submit a support ticket through the full AI Copilot pipeline
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 20 }}>
          {/* Form */}
          <div className="glass-card" style={{ padding: 24 }}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: '0.8rem', color: '#9575cd', display: 'block', marginBottom: 6 }}>
                TICKET DESCRIPTION *
              </label>
              <textarea
                className="input-field"
                rows={5}
                placeholder="Describe the issue in detail…"
                value={text}
                onChange={e => setText(e.target.value)}
                style={{ resize: 'vertical' }}
              />
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: '0.8rem', color: '#9575cd', display: 'block', marginBottom: 6 }}>
                CATEGORY (auto-detected if blank)
              </label>
              <select
                className="input-field"
                value={category}
                onChange={e => setCategory(e.target.value)}
              >
                {CATEGORIES.map(c => (
                  <option key={c} value={c} style={{ background: '#1e1035' }}>
                    {c || '— Auto Detect —'}
                  </option>
                ))}
              </select>
            </div>
            <button
              className="btn-primary"
              type="button"
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
              onClick={() => submit()}
              disabled={loading || !text.trim()}
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              {loading ? 'Processing…' : 'Process via Copilot'}
            </button>
            {error && (
              <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(255,23,68,0.1)',
                border: '1px solid rgba(255,23,68,0.3)', borderRadius: 8, color: '#ff6b6b', fontSize: '0.85rem' }}>
                {error}
              </div>
            )}
          </div>

          {/* Quick samples */}
          <div className="glass-card" style={{ padding: 20 }}>
            <div style={{ fontSize: '0.8rem', color: '#9575cd', marginBottom: 12, fontWeight: 600 }}>
              QUICK SAMPLES
            </div>
            {SAMPLES.map((s, i) => (
              <button
                key={i}
                onClick={() => setText(s)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  width: '100%', textAlign: 'left', padding: '8px 10px',
                  background: 'rgba(123,47,190,0.08)', border: '1px solid rgba(123,47,190,0.2)',
                  borderRadius: 6, color: '#b39ddb', fontSize: '0.78rem',
                  cursor: 'pointer', marginBottom: 8, transition: 'all 0.2s',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'rgba(123,47,190,0.2)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'rgba(123,47,190,0.08)')}
              >
                <ChevronRight size={12} style={{ flexShrink: 0 }} />
                {s.slice(0, 55)}…
              </button>
            ))}
          </div>
        </div>

        {/* Result */}
        <AnimatePresence>
          {result && (
            <motion.div
              id="ticket-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card"
              style={{ padding: 24, marginTop: 20 }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                <ActionBadge action={result.action} />
                <span style={{ color: '#9575cd', fontSize: '0.85rem' }}>
                  Confidence: {(result.confidence * 100).toFixed(0)}% · Latency: {result.latency_ms?.toFixed(0)}ms
                </span>
                <code style={{ marginLeft: 'auto', fontSize: '0.72rem', color: '#6b5b8a' }}>
                  {result.ticket_id?.slice(0, 30)}
                </code>
              </div>

              <ConfidenceBar value={result.confidence} />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16 }}>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#9575cd', marginBottom: 8, fontWeight: 600 }}>
                    RESOLUTION
                  </div>
                  {result.action === 'auto_resolved' && (
                    <div style={{ padding: 12, background: 'rgba(0,230,118,0.08)',
                      border: '1px solid rgba(0,230,118,0.2)', borderRadius: 8,
                      color: '#ede7f6', fontSize: '0.85rem', lineHeight: 1.6 }}>
                      {result.resolution?.resolution}
                      <div style={{ marginTop: 8, fontSize: '0.75rem', color: '#00e676' }}>
                        Source: {result.resolution?.source_article}
                      </div>
                    </div>
                  )}
                  {result.action === 'draft_response' && (
                    <div style={{ padding: 12, background: 'rgba(255,214,0,0.08)',
                      border: '1px solid rgba(255,214,0,0.2)', borderRadius: 8,
                      color: '#ede7f6', fontSize: '0.85rem', lineHeight: 1.6 }}>
                      {result.resolution?.draft}
                    </div>
                  )}
                  {result.action === 'escalated' && (
                    <div style={{ padding: 12, background: 'rgba(255,23,68,0.08)',
                      border: '1px solid rgba(255,23,68,0.2)', borderRadius: 8, fontSize: '0.85rem' }}>
                      <div style={{ color: '#ff6b6b', marginBottom: 4 }}>
                        <strong>Issue:</strong> {result.resolution?.summary?.issue_summary}
                      </div>
                      <div style={{ color: '#ede7f6' }}>
                        <strong>Root Cause:</strong> {result.resolution?.summary?.probable_root_cause}
                      </div>
                      <div style={{ color: '#ffd600', marginTop: 4 }}>
                        Priority: {result.resolution?.summary?.priority?.toUpperCase()}
                      </div>
                      {/* Escalation CTA */}
                      <motion.button
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        onClick={() => setShowEscalation(true)}
                        style={{
                          marginTop: 12, width: '100%', padding: '10px 16px',
                          background: 'linear-gradient(135deg, rgba(255,23,68,0.2), rgba(123,47,190,0.3))',
                          border: '1px solid rgba(255,23,68,0.4)',
                          borderRadius: 8, cursor: 'pointer',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                          color: '#ff6b6b', fontWeight: 700, fontSize: '0.82rem',
                          transition: 'all 0.2s',
                        }}
                      >
                        <Headphones size={15} />
                        Connect to Live Support
                      </motion.button>
                    </div>
                  )}
                </div>

                <div>
                  <div style={{ fontSize: '0.8rem', color: '#9575cd', marginBottom: 8, fontWeight: 600 }}>
                    KB RECOMMENDATIONS
                  </div>
                  {result.recommendations?.map((r: any, i: number) => (
                    <div key={i} style={{ padding: '8px 12px', marginBottom: 8,
                      background: 'rgba(123,47,190,0.1)', borderRadius: 8,
                      border: '1px solid rgba(123,47,190,0.2)',
                      display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: '0.82rem', color: '#ede7f6' }}>📄 {r.article_title}</div>
                        <div style={{ fontSize: '0.72rem', color: '#9575cd', marginTop: 2 }}>
                          {(r.score * 100).toFixed(0)}% match
                        </div>
                      </div>
                      <FeedbackButtons ticketId={result.ticket_id} articleTitle={r.article_title} />
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Escalation Modal */}
      {result && result.action === 'escalated' && (
        <EscalationModal
          open={showEscalation}
          onClose={() => setShowEscalation(false)}
          context={{
            ticketId: result.ticket_id || '',
            ticketText: text || result.resolution?.summary?.issue_summary || '',
            category: result.category || '',
            confidence: result.confidence || 0,
            urgency: result.resolution?.summary?.priority || 'high',
            aiResolution: result.resolution?.summary?.attempted_fixes || 'KB semantic search — low confidence',
            rootCause: result.resolution?.summary?.probable_root_cause || 'Requires investigation',
            kbArticles: result.recommendations || [],
          }}
        />
      )}
    </div>
  )
}
