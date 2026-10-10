import { motion } from 'framer-motion'
import { FileText, ExternalLink } from 'lucide-react'

interface Props {
  title: string
  score: number
  rank: number
  delay?: number
}

export function RecommendationCard({ title, score, rank, delay = 0 }: Props) {
  const pct = Math.round(score * 100)
  const color = pct >= 85 ? '#00e676' : pct >= 60 ? '#ffd600' : '#ff6b6b'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.35 }}
      style={{
        background: 'linear-gradient(135deg, rgba(30,16,53,0.9) 0%, rgba(26,10,46,0.9) 100%)',
        border: '1px solid rgba(123,47,190,0.25)',
        borderRadius: 10,
        padding: '14px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        transition: 'all 0.2s',
        cursor: 'pointer',
      }}
      whileHover={{
        borderColor: 'rgba(123,47,190,0.5)',
        boxShadow: '0 4px 20px rgba(123,47,190,0.15)',
        y: -2,
      }}
    >
      {/* Rank badge */}
      <div style={{
        width: 28, height: 28, borderRadius: 8,
        background: 'rgba(123,47,190,0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '0.75rem', fontWeight: 800, color: '#9575cd',
        flexShrink: 0,
      }}>
        #{rank}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: '0.82rem', color: '#ede7f6', fontWeight: 600,
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          display: 'flex', alignItems: 'center', gap: 6,
        }}>
          <FileText size={13} color="#9575cd" />
          {title}
        </div>
        <div style={{ fontSize: '0.72rem', color: '#6b5b8a', marginTop: 2 }}>
          Semantic match
        </div>
      </div>

      {/* Score */}
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div style={{ fontSize: '1rem', fontWeight: 800, color }}>
          {pct}%
        </div>
        <div style={{ fontSize: '0.65rem', color: '#6b5b8a' }}>confidence</div>
      </div>

      <ExternalLink size={12} color="#4a3570" style={{ flexShrink: 0 }} />
    </motion.div>
  )
}
