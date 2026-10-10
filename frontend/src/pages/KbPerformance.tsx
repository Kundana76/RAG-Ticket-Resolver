import { useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { usePolling } from '../hooks/usePolling'
import { api } from '../services/api'
import type { FeedbackStats } from '../services/api'

const TOOLTIP_STYLE = {
  backgroundColor: '#1e1035', border: '1px solid rgba(123,47,190,0.3)',
  borderRadius: 8, color: '#ede7f6', fontSize: 12,
}

export function KbPerformance() {
  const [data, setData] = useState<any[]>([])
  const [fb, setFb] = useState<FeedbackStats | null>(null)

  usePolling(async () => {
    try { setData(await api.getKbPerformance()) } catch {}
    try { setFb(await api.getFeedbackStats()) } catch {}
  }, 8000)

  const chartData = data.map(d => ({
    article: d.article?.slice(0, 28) + (d.article?.length > 28 ? '…' : ''),
    impressions: d.impressions,
    avg_score: Math.round(d.avg_score * 100),
  }))

  return (
    <div style={{ padding: 28 }}>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ede7f6', marginBottom: 4 }}>
          📈 KB Article Performance
        </h1>
        <p style={{ color: '#9575cd', marginBottom: 24, fontSize: '0.9rem' }}>
          Valkey Sorted Set — ZINCRBY analytics:kb:impressions
        </p>

        {data.length > 0 ? (
          <>
            <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ede7f6', marginBottom: 16 }}>
                Top Articles by Impressions
              </h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={chartData} layout="vertical">
                  <XAxis type="number" tick={{ fill: '#9575cd', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="article" tick={{ fill: '#9575cd', fontSize: 10 }}
                    axisLine={false} tickLine={false} width={200} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="impressions" radius={[0, 4, 4, 0]}>
                    {chartData.map((_, i) => (
                      <Cell key={i} fill={i < 3 ? '#7B2FBE' : '#4a2080'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="glass-card" style={{ padding: 20 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(123,47,190,0.2)' }}>
                    {['Article', 'Impressions', 'Avg Score'].map(h => (
                      <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#9575cd',
                        fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: 1 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(123,47,190,0.08)' }}>
                      <td style={{ padding: '8px 12px', color: '#ede7f6' }}>📄 {row.article}</td>
                      <td style={{ padding: '8px 12px', color: '#b39ddb', fontWeight: 700 }}>{row.impressions}</td>
                      <td style={{ padding: '8px 12px' }}>
                        <span style={{
                          color: row.avg_score > 0.7 ? '#00e676' : row.avg_score > 0.5 ? '#ffd600' : '#ff6b6b',
                          fontWeight: 700,
                        }}>
                          {(row.avg_score * 100).toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="glass-card" style={{ padding: 60, textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', marginBottom: 12 }}>📊</div>
            <div style={{ color: '#6b5b8a', fontSize: '0.9rem' }}>
              No KB performance data yet.<br />Process tickets to generate article metrics.
            </div>
          </div>
        )}

        {fb && fb.total_votes > 0 && (
          <div className="glass-card" style={{ padding: 20, marginTop: 20 }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ede7f6', marginBottom: 4 }}>
              Was it helpful? Feedback
            </h3>
            <p style={{ color: '#9575cd', fontSize: '0.8rem', marginBottom: 14 }}>
              {fb.total_votes} votes, {Math.round((fb.helpful_rate ?? 0) * 100)}% helpful. After 3+ votes an article's
              match score shifts by up to ±10 points.
            </p>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(123,47,190,0.2)' }}>
                  {['Article', 'Helpful', 'Not helpful', 'Score shift'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#9575cd',
                      fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: 1 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {fb.articles.map(a => (
                  <tr key={a.article_title} style={{ borderBottom: '1px solid rgba(123,47,190,0.08)' }}>
                    <td style={{ padding: '8px 12px', color: '#ede7f6' }}>{a.article_title}</td>
                    <td style={{ padding: '8px 12px', color: '#00e676', fontWeight: 700 }}>{a.helpful}</td>
                    <td style={{ padding: '8px 12px', color: '#ff6b6b', fontWeight: 700 }}>{a.unhelpful}</td>
                    <td style={{ padding: '8px 12px', color: '#b39ddb' }}>
                      {a.adjustment === 0 ? '—' : `${a.adjustment > 0 ? '+' : ''}${(a.adjustment * 100).toFixed(1)} pts`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>
    </div>
  )
}
