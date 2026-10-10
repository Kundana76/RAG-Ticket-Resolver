import { motion } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'
import { Ticket, CheckCircle, AlertTriangle, Users, Zap, TrendingUp } from 'lucide-react'
import { useStore } from '../store/useStore'
import { api } from '../services/api'
import { usePolling } from '../hooks/usePolling'
import { MetricCard } from '../components/MetricCard'
import { IncidentBanner } from '../components/IncidentBanner'
import { LiveActivityFeed } from '../components/LiveActivityFeed'

const TOOLTIP_STYLE = {
  backgroundColor: '#1e1035',
  border: '1px solid rgba(123,47,190,0.3)',
  borderRadius: 8,
  color: '#ede7f6',
  fontSize: 12,
}

export function Dashboard() {
  const { metrics, setMetrics, activityFeed, setActivityFeed,
          trending, setTrending, hourlyTrend, setHourlyTrend,
          setApiConnected, setEscalationQueueLength } = useStore()

  const refresh = async () => {
    try {
      const [dash, feed] = await Promise.all([
        api.getDashboard(),
        api.getActivityFeed(15),
      ])
      setMetrics(dash.live)
      setActivityFeed(feed)
      setTrending(dash.trending || [])
      setHourlyTrend(dash.hourly_trend || [])
      setEscalationQueueLength(dash.escalation_queue_length || 0)
      setApiConnected(true)
    } catch {
      setApiConnected(false)
    }
  }

  usePolling(refresh, 5000)

  const spikes = trending.filter(t => t.is_spike)

  return (
    <div style={{ padding: 28 }}>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ede7f6', marginBottom: 4 }}>
              AI Operations Dashboard
            </h1>
            <p style={{ color: '#9575cd', fontSize: '0.85rem' }}>
              Real-time support intelligence — powered by Valkey
            </p>
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '6px 14px', borderRadius: 20,
            background: 'rgba(0,230,118,0.1)',
            border: '1px solid rgba(0,230,118,0.25)',
          }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00e676', boxShadow: '0 0 8px #00e676' }} />
            <span style={{ fontSize: '0.72rem', color: '#00e676', fontWeight: 600 }}>SYSTEM ONLINE</span>
          </div>
        </div>

        <IncidentBanner spikes={spikes} />

        {/* KPI Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: 14, marginBottom: 24 }}>
          <MetricCard label="Tickets Today"    value={metrics?.total_tickets_today ?? 0} icon={Ticket}      color="purple" delay={0} />
          <MetricCard label="Auto-Resolved"    value={metrics?.auto_resolved ?? 0}       icon={CheckCircle} color="green"  delay={0.05} />
          <MetricCard label="Resolution Rate"  value={`${metrics?.auto_resolution_rate ?? 0}%`} icon={TrendingUp} color="green" delay={0.1} />
          <MetricCard label="Escalated"        value={metrics?.escalated ?? 0}           icon={AlertTriangle} color="red"  delay={0.15} />
          <MetricCard label="Escalation Rate"  value={`${metrics?.escalation_rate ?? 0}%`} icon={Zap}       color="amber" delay={0.2} />
          <MetricCard label="Active Users"     value={metrics?.active_users ?? 0}        icon={Users}       color="purple" delay={0.25} />
        </div>

        {/* Charts Row */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 24 }}>
          {/* Hourly trend */}
          <div className="glass-card" style={{ padding: 20 }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ede7f6', marginBottom: 16 }}>
              📈 Hourly Ticket Volume
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={hourlyTrend} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(123,47,190,0.12)" vertical={false} />
                <XAxis dataKey="hour" tick={{ fill: '#9575cd', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#9575cd', fontSize: 10 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'rgba(123,47,190,0.08)' }} />
                <Bar dataKey="total" name="Total" fill="#7B2FBE" radius={[4, 4, 0, 0]} maxBarSize={28} />
                <Bar dataKey="auto_resolved" name="Resolved" fill="#00e676" radius={[4, 4, 0, 0]} maxBarSize={28} />
                <Bar dataKey="escalated" name="Escalated" fill="#ff1744" radius={[4, 4, 0, 0]} maxBarSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Trending */}
          <div className="glass-card" style={{ padding: 20 }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ede7f6', marginBottom: 16 }}>
              🔥 Trending Now
            </h3>
            {trending.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={trending.slice(0, 6)} layout="vertical">
                  <XAxis type="number" tick={{ fill: '#9575cd', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="category" tick={{ fill: '#9575cd', fontSize: 10 }}
                    axisLine={false} tickLine={false} width={100}
                    tickFormatter={v => v.replace(/_/g, ' ')} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="score" fill="#7B2FBE" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ color: '#6b5b8a', fontSize: '0.85rem', textAlign: 'center', paddingTop: 60 }}>
                No trending data yet.<br />Process tickets to see spikes.
              </div>
            )}
          </div>
        </div>

        {/* Activity Feed */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <LiveActivityFeed items={activityFeed} />

          {/* Category breakdown */}
          <div className="glass-card p-5">
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ede7f6', marginBottom: 16 }}>
              Category Distribution
            </h3>
            {metrics?.categories && Object.keys(metrics.categories).length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {Object.entries(metrics.categories)
                  .sort(([,a], [,b]) => (b as number) - (a as number))
                  .map(([cat, count]) => {
                    const total = metrics.total_tickets_today || 1
                    const pct = Math.round(((count as number) / total) * 100)
                    return (
                      <div key={cat}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                          <span style={{ fontSize: '0.78rem', color: '#b39ddb' }}>
                            {cat.replace(/_/g, ' ')}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: '#9575cd', fontWeight: 600 }}>
                            {count as number} ({pct}%)
                          </span>
                        </div>
                        <div style={{ height: 4, borderRadius: 2, background: 'rgba(123,47,190,0.15)' }}>
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.6, delay: 0.1 }}
                            style={{ height: '100%', borderRadius: 2, background: '#7B2FBE' }}
                          />
                        </div>
                      </div>
                    )
                  })}
              </div>
            ) : (
              <div style={{ color: '#6b5b8a', fontSize: '0.82rem', textAlign: 'center', paddingTop: 40 }}>
                No category data yet.
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
