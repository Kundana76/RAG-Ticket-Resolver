import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle } from 'lucide-react'

interface Props { spikes: Array<{ category: string; score: number }> }

export function SpikeBanner({ spikes }: Props) {
  if (!spikes.length) return null
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="spike-banner flex items-center gap-3 mb-4"
      >
        <AlertTriangle size={18} color="#ff1744" />
        <span className="font-bold text-sm" style={{ color: '#ff6b6b' }}>
          INCIDENT SPIKE DETECTED:
        </span>
        <span className="text-sm" style={{ color: '#ede7f6' }}>
          {spikes.map(s => `${s.category.replace(/_/g, ' ').toUpperCase()} (${s.score} hits)`).join(' · ')}
        </span>
      </motion.div>
    </AnimatePresence>
  )
}
