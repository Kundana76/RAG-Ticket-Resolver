import { motion } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'

interface Props {
  label: string
  value: string | number
  icon: LucideIcon
  color?: 'green' | 'red' | 'amber' | 'purple'
  subtitle?: string
  delay?: number
}

const colorMap = {
  green:  { text: '#00e676', glow: 'rgba(0,230,118,0.15)',  border: 'rgba(0,230,118,0.25)' },
  red:    { text: '#ff1744', glow: 'rgba(255,23,68,0.15)',  border: 'rgba(255,23,68,0.25)' },
  amber:  { text: '#ffd600', glow: 'rgba(255,214,0,0.15)',  border: 'rgba(255,214,0,0.25)' },
  purple: { text: '#b39ddb', glow: 'rgba(123,47,190,0.15)', border: 'rgba(123,47,190,0.3)' },
}

export function MetricCard({ label, value, icon: Icon, color = 'purple', subtitle, delay = 0 }: Props) {
  const c = colorMap[color]
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="glass-card p-5"
      style={{ boxShadow: `0 0 24px ${c.glow}`, borderColor: c.border }}
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#9575cd' }}>
          {label}
        </span>
        <Icon size={18} style={{ color: c.text }} />
      </div>
      <motion.div
        key={String(value)}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="text-3xl font-bold"
        style={{ color: c.text }}
      >
        {value}
      </motion.div>
      {subtitle && (
        <div className="text-xs mt-1" style={{ color: '#6b5b8a' }}>{subtitle}</div>
      )}
    </motion.div>
  )
}
