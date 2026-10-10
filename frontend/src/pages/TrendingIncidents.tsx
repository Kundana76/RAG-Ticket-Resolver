import { useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useStore } from '../store/useStore'
import { api } from '../services/api'
import { usePolling } from '../hooks/usePolling'
import { SpikeBanner } from '../components/SpikeBanner'

const TOOLTIP_STYLE = {
  backgroundColor: '#1e1035', border: '1px solid rgba(123,47,190,0.3)',
  borderRadius: 8, color: '#ede7f6', fontSize: 12,
}

export function TrendingIncidents() {
  const { trending, setTrending } = useStore()
  const [window, setWindow] = useState<'1h' | '24h'>('1h')
  const [allScores, setAllScores] = useState<Record<string, number>>({})

  const refresh = async () => {
    try {
      const d = await api.getTrending(window)
      setTrending(d.trending || [])
      setAllScores(d.all_scores || {})
    } catch {}
  }

  usePolling(refresh, 5000)

  const spikes = trending.filter(t => t.is_spike)
  const chartData = Object.entries(allScores)
    .map(([category, score]) => ({ category: category.replace(/_/g, ' '), score }))
    .sort((a, b) => b.score - a.score)

  return (
    <div style={{ padding: 28 }}>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ede7f6', marginBottom: 4 }}>
          🔥 Trending Incidents
        </h1>
        <p style={{ color: '#9575cd', marginBottom: 20, fontSize: '0.9rem' }}>
          Valkey Sorted Sets — ZINCRBY / ZREVRANGE with weighted scoring
        </p>

        <SpikeBanner spikes={spikes} />

        {/* Window toggle */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          {(['1h', '24h'] as const).map(w => (
            <button key={w} onClick={() => setWindow(w)} style={{
              padding: '6px 16px', borderRadius: 20,
              background: window === w ? '#7B2FBE' : 'rgba(123,47,190,0.15)',
              border: `1px solid ${window === w ? '#7B2FBE' : 'rgba(123,47,190,0.3)'}`,
              color: window === w ? 'white' : '#9575cd',
              cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600,
            }}>
              {w}
            </button>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
          {/* Bar chart */}
          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ede7f6', marginBottom: 16 }}>
              All-Time Category Scores
            </h3>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={chartData} layout="vertical">
                  <XAxis type="number" tick={{ fill: '#9575cd', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="category" tick={{ fill: '#9575cd', fontSize: 11 }}
                    axisLine={false} tickLine={false} width={140} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {chartData.map((_, i) => (
                      <Cell key={i} fill={i === 0 ? '#ff1744' : i === 1 ? '#ff6b6b' : '#7B2FBE'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ color: '#6b5b8a', textAlign: 'center', padding: '60px 0', fontSize: '0.85rem' }}>
                No trending data yet. Process tickets to see incident scores.
              </div>
            )}
          </div>

          {/* Trending list */}
          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ede7f6', marginBottom: 16 }}>
              Current Trending ({window})
            </h3>
            {trending.length > 0 ? (
              trending.map((t, i) => (
                <motion.div
                  key={t.category}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '10px 12px', marginBottom: 8, borderRadius: 8,
                    background: t.is_spike ? 'rgba(255,23,68,0.1)' : 'rgba(123,47,190,0.08)',
                    border: `1px solid ${t.is_spike ? 'rgba(255,23,68,0.3)' : 'rgba(123,47,190,0.2)'}`,
                  }}
                >
                  <span style={{ fontSize: '1rem' }}>{t.is_spike ? '🔴' : '🟡'}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.82rem', color: '#ede7f6', fontWeight: 600 }}>
                      {t.category.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: '#9575cd' }}>
                      Score: {t.score} {t.is_spike ? '· SPIKE' : ''}
                    </div>
                  </div>
                  {t.is_spike && (
                    <span style={{ background: '#ff1744', color: 'white',
                      padding: '2px 8px', borderRadius: 10, fontSize: '0.65rem', fontWeight: 700 }}>
                      SPIKE
                    </span>
                  )}
                </motion.div>
              ))
            ) : (
              <div style={{ color: '#6b5b8a', fontSize: '0.85rem', textAlign: 'center', paddingTop: 40 }}>
                No trending data in this window.
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
