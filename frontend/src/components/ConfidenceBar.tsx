import { motion } from 'framer-motion'

interface Props { value: number; showLabel?: boolean }

export function ConfidenceBar({ value, showLabel = true }: Props) {
  const pct = Math.round(value * 100)
  const color = value >= 0.85 ? '#00e676' : value >= 0.5 ? '#ffd600' : '#ff1744'
  return (
    <div>
      {showLabel && (
        <div className="flex justify-between text-xs mb-1" style={{ color: '#9575cd' }}>
          <span>Confidence</span>
          <span style={{ color }}>{pct}%</span>
        </div>
      )}
      <div className="confidence-bar">
        <motion.div
          className="confidence-fill"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          style={{ background: color }}
        />
      </div>
    </div>
  )
}
