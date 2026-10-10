import { motion, AnimatePresence } from 'framer-motion'
import { Bot, Zap, AlertTriangle, CheckCircle, FileText } from 'lucide-react'
import type { ActivityItem } from '../services/api'

interface Props { items: ActivityItem[] }

const ICONS: Record<string, { icon: typeof Bot; color: string }> = {
  auto_resolved:  { icon: CheckCircle,   color: '#00e676' },
  escalated:      { icon: AlertTriangle,  color: '#ff1744' },
  draft_response: { icon: FileText,       color: '#ffd600' },
}

function formatAction(action: string): string {
  switch (action) {
    case 'auto_resolved':  return '[AI] Auto-resolution triggered'
    case 'escalated':      return '[SYSTEM] Escalated to human agent'
    case 'draft_response': return '[AI] Draft response generated'
    default:               return '[AI] Ticket processed'
  }
}

export function LiveActivityFeed({ items }: Props) {
  return (
    <div className="glass-card p-5" style={{ maxHeight: 420, overflowY: 'auto' }}>
      <div className="flex items-center gap-2 mb-4">
        <Zap size={14} color="#7B2FBE" />
        <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ede7f6' }}>
          Live AI Activity Feed
        </h3>
        <div style={{
          width: 6, height: 6, borderRadius: '50%',
          background: '#00e676', marginLeft: 'auto',
          boxShadow: '0 0 8px #00e676',
          animation: 'pulse 2s infinite',
        }} />
      </div>

      {items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '30px 0', color: '#6b5b8a', fontSize: '0.82rem' }}>
          <Bot size={28} style={{ margin: '0 auto 8px', opacity: 0.4 }} />
          Waiting for activity…
        </div>
      ) : (
        <AnimatePresence mode="popLayout">
          {items.slice(0, 15).map((item, i) => {
            const { icon: Icon, color } = ICONS[item.action] || ICONS.draft_response
            return (
              <motion.div
                key={item.id || `${item.ticket_id}-${i}`}
                initial={{ opacity: 0, x: -20, height: 0 }}
                animate={{ opacity: 1, x: 0, height: 'auto' }}
                exit={{ opacity: 0, x: 20, height: 0 }}
                transition={{ duration: 0.3, delay: i * 0.02 }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '8px 10px', marginBottom: 6, borderRadius: 8,
                  background: 'rgba(123,47,190,0.06)',
                  borderLeft: `2px solid ${color}`,
                }}
              >
                <Icon size={13} color={color} style={{ flexShrink: 0 }} />
                <span style={{ fontSize: '0.78rem', color: '#b39ddb', flex: 1 }}>
                  {formatAction(item.action)}
                </span>
                <span style={{ fontSize: '0.7rem', color: '#6b5b8a', fontFamily: 'monospace' }}>
                  {item.category?.replace(/_/g, ' ')}
                </span>
                <span style={{ fontSize: '0.68rem', color: '#4a3570' }}>
                  {item.timestamp?.slice(11, 19)}
                </span>
              </motion.div>
            )
          })}
        </AnimatePresence>
      )}
    </div>
  )
}
