import { useState } from 'react'
import { motion } from 'framer-motion'
import { Zap, Trash2, Loader2, CheckCircle } from 'lucide-react'
import { api, errorMessage } from '../services/api'

export function DemoControls() {
  const [loading, setLoading] = useState<string | null>(null)
  const [result, setResult] = useState<string | null>(null)

  const run = async (key: string, fn: () => Promise<any>, msg: string) => {
    setLoading(key); setResult(null)
    try {
      const r = await fn()
      setResult(msg + (r?.processed ? ` (${r.processed} tickets)` : ''))
    } catch (e) {
      setResult(errorMessage(e, 'Error — is the API running?'))
    } finally {
      setLoading(null)
    }
  }

  const VALKEY_KEYS = [
    { key: 'conversation:{id}',           type: 'JSON',       challenge: '14', purpose: 'Full ticket lifecycle' },
    { key: 'trending:global:1h',          type: 'Sorted Set', challenge: '4',  purpose: 'Weighted incident scores' },
    { key: 'trending:global:24h',         type: 'Sorted Set', challenge: '4',  purpose: '24h trending window' },
    { key: 'metrics:orders:count:{ts}',   type: 'String',     challenge: '8',  purpose: 'Per-minute order counter' },
    { key: 'metrics:revenue:{ts}',        type: 'Hash',       challenge: '8',  purpose: 'Hourly action breakdown' },
    { key: 'active_users:{date}:{hour}',  type: 'HyperLogLog',challenge: '8',  purpose: 'Unique user count' },
    { key: 'stream:ticket:events',        type: 'Stream',     challenge: '8',  purpose: 'Event pipeline (cap 1000)' },
    { key: 'analytics:kb:impressions',    type: 'Sorted Set', challenge: '8',  purpose: 'KB article impressions' },
    { key: 'escalation:queue',            type: 'List',       challenge: '—',  purpose: 'FIFO escalation queue' },
    { key: 'ratelimit:{user}:{ep}:{w}',   type: 'Sorted Set', challenge: '12', purpose: 'Sliding window rate limit' },
    { key: 'agent_cache:{hash}',          type: 'String',     challenge: '14', purpose: 'Agent result cache (5min)' },
  ]

  return (
    <div style={{ padding: 28 }}>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ede7f6', marginBottom: 4 }}>
          ⚡ Demo Controls
        </h1>
        <p style={{ color: '#9575cd', marginBottom: 24, fontSize: '0.9rem' }}>
          Hackathon demo tools — populate data, reset, inspect Valkey schema
        </p>

        {result && (
          <div style={{ marginBottom: 20, padding: '12px 16px',
            background: 'rgba(0,230,118,0.1)', border: '1px solid rgba(0,230,118,0.2)',
            borderRadius: 8, color: '#00e676', display: 'flex', alignItems: 'center', gap: 8 }}>
            <CheckCircle size={16} /> {result}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 28 }}>
          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ede7f6', marginBottom: 8 }}>
              🚀 Populate Dashboard
            </h3>
            <p style={{ fontSize: '0.82rem', color: '#9575cd', marginBottom: 16 }}>
              Process all 12 sample tickets to fill the dashboard with live data, trending scores, and escalations.
            </p>
            <button
              className="btn-primary"
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
              disabled={loading === 'batch'}
              onClick={() => run('batch', async () => {
                const samples = await api.getSampleTickets()
                return api.batchProcess(samples)
              }, '✅ Processed all sample tickets')}
            >
              {loading === 'batch' ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
              {loading === 'batch' ? 'Processing…' : 'Process All Sample Tickets'}
            </button>
          </div>

          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ede7f6', marginBottom: 8 }}>
              🗑️ Reset Demo Data
            </h3>
            <p style={{ fontSize: '0.82rem', color: '#9575cd', marginBottom: 16 }}>
              Clear all Valkey keys — trending scores, analytics counters, escalation queue, conversation memory.
            </p>
            <button
              style={{
                width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                padding: '10px 20px', borderRadius: 8, fontWeight: 600, cursor: 'pointer',
                background: 'rgba(255,23,68,0.15)', border: '1px solid rgba(255,23,68,0.3)',
                color: '#ff6b6b', transition: 'all 0.2s',
              }}
              disabled={loading === 'reset'}
              onClick={() => run('reset', api.resetDemo, '✅ All Valkey data cleared')}
            >
              {loading === 'reset' ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
              {loading === 'reset' ? 'Resetting…' : 'Reset All Valkey Data'}
            </button>
          </div>
        </div>

        {/* Valkey schema */}
        <div className="glass-card" style={{ padding: 24 }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ede7f6', marginBottom: 16 }}>
            🏗️ Valkey Data Structure Map
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(123,47,190,0.3)' }}>
                  {['Key Pattern', 'Type', 'Challenge', 'Purpose'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#9575cd',
                      fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: 1 }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {VALKEY_KEYS.map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(123,47,190,0.1)' }}>
                    <td style={{ padding: '8px 12px' }}>
                      <code style={{ color: '#b39ddb', fontSize: '0.78rem' }}>{row.key}</code>
                    </td>
                    <td style={{ padding: '8px 12px', color: '#7B2FBE', fontWeight: 600 }}>{row.type}</td>
                    <td style={{ padding: '8px 12px', color: '#9575cd' }}>{row.challenge}</td>
                    <td style={{ padding: '8px 12px', color: '#ede7f6' }}>{row.purpose}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: 16, padding: '12px 16px', background: 'rgba(123,47,190,0.1)',
            borderRadius: 8, fontSize: '0.8rem', color: '#9575cd' }}>
            <strong style={{ color: '#b39ddb' }}>Valkey image:</strong>{' '}
            <code style={{ color: '#7B2FBE' }}>valkey/valkey-bundle:9-alpine</code>
            <br />
            <code style={{ color: '#6b5b8a' }}>
              docker run -d --name valkey -p 6379:6379 valkey/valkey-bundle:9-alpine
            </code>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
