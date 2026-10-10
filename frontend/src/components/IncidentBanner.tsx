import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, TrendingUp } from 'lucide-react'
import type { TrendingItem } from '../services/api'

interface Props { spikes: TrendingItem[] }

export function IncidentBanner({ spikes }: Props) {
  if (!spikes.length) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -12, scaleY: 0.9 }}
        animate={{ opacity: 1, y: 0, scaleY: 1 }}
        exit={{ opacity: 0, y: -12 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        style={{
          background: 'linear-gradient(135deg, rgba(255,23,68,0.12) 0%, rgba(183,28,28,0.08) 100%)',
          border: '1px solid rgba(255,23,68,0.35)',
          borderLeft: '4px solid #ff1744',
          borderRadius: 10,
          padding: '14px 18px',
          marginBottom: 16,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
        }}
      >
        <motion.div
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ repeat: Infinity, duration: 2 }}
        >
          <AlertTriangle size={20} color="#ff1744" />
        </motion.div>

        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#ff6b6b', letterSpacing: 0.5, marginBottom: 2 }}>
            ⚠ INCIDENT SPIKE DETECTED
          </div>
          <div style={{ fontSize: '0.82rem', color: '#ede7f6', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            {spikes.map(s => (
              <span key={s.category} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <TrendingUp size={12} color="#ff1744" />
                <strong>{s.category.replace(/_/g, ' ')}</strong>
                <span style={{ color: '#ff6b6b' }}>({s.score} hits)</span>
              </span>
            ))}
          </div>
        </div>

        <div style={{
          background: 'rgba(255,23,68,0.2)',
          padding: '4px 10px',
          borderRadius: 20,
          fontSize: '0.68rem',
          fontWeight: 700,
          color: '#ff6b6b',
          letterSpacing: 1,
        }}>
          LIVE
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
