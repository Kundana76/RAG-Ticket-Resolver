/**
 * Escalation Modal — Premium AI-to-Human handoff experience.
 * 
 * Shown when AI confidence < 70% (escalation triggered).
 * Displays full context and provides "Connect to Live Support" button
 * that opens Tawk.to with pre-filled escalation context.
 */
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertTriangle, Headphones, X, Brain, FileText,
  TrendingDown, Shield, ArrowRight, Loader2
} from 'lucide-react'
import { useState } from 'react'
import { useTawkTo, type EscalationContext } from '../hooks/useTawkTo'

interface Props {
  open: boolean
  onClose: () => void
  context: {
    ticketId: string
    ticketText: string
    category: string
    confidence: number
    urgency: string
    aiResolution: string
    rootCause: string
    kbArticles: Array<{ title: string; score: number }>
  }
}

export function EscalationModal({ open, onClose, context }: Props) {
  const { escalate, isConfigured } = useTawkTo()
  const [connecting, setConnecting] = useState(false)

  const handleConnect = () => {
    setConnecting(true)

    const escalationCtx: EscalationContext = {
      ticketId: context.ticketId,
      ticketText: context.ticketText,
      category: context.category,
      confidence: context.confidence,
      urgency: context.urgency,
      aiResolution: context.aiResolution,
      kbArticles: context.kbArticles.map(a => a.title),
    }

    // Small delay for animation feel
    setTimeout(() => {
      escalate(escalationCtx)
      setConnecting(false)
      onClose()
    }, 800)
  }

  const confidencePct = Math.round(context.confidence * 100)

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed', inset: 0, zIndex: 1000,
              background: 'rgba(0,0,0,0.7)',
              backdropFilter: 'blur(4px)',
            }}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 28 }}
            style={{
              position: 'fixed', top: '50%', left: '50%',
              transform: 'translate(-50%, -50%)',
              zIndex: 1001, width: '100%', maxWidth: 560,
              background: 'linear-gradient(135deg, #1e1035 0%, #0d0720 100%)',
              border: '1px solid rgba(255,23,68,0.3)',
              borderRadius: 16, overflow: 'hidden',
              boxShadow: '0 0 60px rgba(255,23,68,0.15), 0 20px 60px rgba(0,0,0,0.5)',
            }}
          >
            {/* Header glow bar */}
            <div style={{
              height: 3,
              background: 'linear-gradient(90deg, #ff1744, #ff6b6b, #ff1744)',
              animation: 'pulse-glow 2s infinite',
            }} />

            {/* Close button */}
            <button
              onClick={onClose}
              style={{
                position: 'absolute', top: 16, right: 16,
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 8, padding: 6, cursor: 'pointer',
                color: '#9575cd', transition: 'all 0.2s',
              }}
            >
              <X size={16} />
            </button>

            <div style={{ padding: '28px 28px 24px' }}>
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ repeat: Infinity, duration: 2 }}
                  style={{
                    width: 44, height: 44, borderRadius: 12,
                    background: 'rgba(255,23,68,0.15)',
                    border: '1px solid rgba(255,23,68,0.3)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}
                >
                  <AlertTriangle size={22} color="#ff1744" />
                </motion.div>
                <div>
                  <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#ede7f6', margin: 0 }}>
                    Human Assistance Recommended
                  </h2>
                  <p style={{ fontSize: '0.8rem', color: '#9575cd', margin: '2px 0 0' }}>
                    AI confidence below threshold — escalating to live support
                  </p>
                </div>
              </div>

              {/* Context cards */}
              <div style={{
                display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10,
                marginBottom: 18,
              }}>
                {/* Confidence */}
                <div style={{
                  padding: '12px 14px', borderRadius: 10,
                  background: 'rgba(255,23,68,0.08)',
                  border: '1px solid rgba(255,23,68,0.2)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <TrendingDown size={12} color="#ff6b6b" />
                    <span style={{ fontSize: '0.7rem', color: '#ff6b6b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                      AI Confidence
                    </span>
                  </div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ff1744' }}>
                    {confidencePct}%
                  </div>
                </div>

                {/* Category */}
                <div style={{
                  padding: '12px 14px', borderRadius: 10,
                  background: 'rgba(123,47,190,0.08)',
                  border: '1px solid rgba(123,47,190,0.2)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <Brain size={12} color="#9575cd" />
                    <span style={{ fontSize: '0.7rem', color: '#9575cd', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                      Category
                    </span>
                  </div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#b39ddb' }}>
                    {context.category.replace(/_/g, ' ')}
                  </div>
                </div>

                {/* Urgency */}
                <div style={{
                  padding: '12px 14px', borderRadius: 10,
                  background: 'rgba(255,214,0,0.06)',
                  border: '1px solid rgba(255,214,0,0.2)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <Shield size={12} color="#ffd600" />
                    <span style={{ fontSize: '0.7rem', color: '#ffd600', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                      Priority
                    </span>
                  </div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ffd600' }}>
                    {(context.urgency || 'HIGH').toUpperCase()}
                  </div>
                </div>

                {/* Root Cause */}
                <div style={{
                  padding: '12px 14px', borderRadius: 10,
                  background: 'rgba(123,47,190,0.06)',
                  border: '1px solid rgba(123,47,190,0.15)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <FileText size={12} color="#7B2FBE" />
                    <span style={{ fontSize: '0.7rem', color: '#7B2FBE', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                      Root Cause
                    </span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#b39ddb', lineHeight: 1.4 }}>
                    {context.rootCause?.slice(0, 60) || 'Requires investigation'}
                  </div>
                </div>
              </div>

              {/* Ticket summary */}
              <div style={{
                padding: '12px 14px', borderRadius: 10, marginBottom: 18,
                background: 'rgba(123,47,190,0.05)',
                border: '1px solid rgba(123,47,190,0.15)',
              }}>
                <div style={{ fontSize: '0.7rem', color: '#9575cd', fontWeight: 600, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  Ticket Summary
                </div>
                <div style={{ fontSize: '0.82rem', color: '#ede7f6', lineHeight: 1.5 }}>
                  {context.ticketText.slice(0, 200)}
                </div>
              </div>

              {/* KB articles attempted */}
              {context.kbArticles.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <div style={{ fontSize: '0.7rem', color: '#9575cd', fontWeight: 600, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    AI Attempted Resolution With
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {context.kbArticles.slice(0, 3).map((a, i) => (
                      <div key={i} style={{
                        display: 'flex', alignItems: 'center', gap: 8,
                        padding: '6px 10px', borderRadius: 6,
                        background: 'rgba(123,47,190,0.06)',
                        fontSize: '0.78rem', color: '#b39ddb',
                      }}>
                        <FileText size={11} color="#6b5b8a" />
                        <span style={{ flex: 1 }}>{a.title}</span>
                        <span style={{ color: '#6b5b8a', fontSize: '0.7rem' }}>
                          {(a.score * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Connect button */}
              <motion.button
                whileHover={{ scale: 1.02, boxShadow: '0 0 30px rgba(123,47,190,0.4)' }}
                whileTap={{ scale: 0.98 }}
                onClick={handleConnect}
                disabled={connecting}
                style={{
                  width: '100%', padding: '14px 20px',
                  background: 'linear-gradient(135deg, #7B2FBE 0%, #9B59D0 100%)',
                  border: 'none', borderRadius: 10,
                  color: 'white', fontWeight: 700, fontSize: '0.9rem',
                  cursor: connecting ? 'wait' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
                  transition: 'all 0.2s',
                  opacity: connecting ? 0.8 : 1,
                }}
              >
                {connecting ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Connecting to Live Support…
                  </>
                ) : (
                  <>
                    <Headphones size={18} />
                    Connect to Live Support
                    <ArrowRight size={16} />
                  </>
                )}
              </motion.button>

              {!isConfigured && (
                <div style={{
                  marginTop: 10, padding: '8px 12px', borderRadius: 6,
                  background: 'rgba(255,214,0,0.08)',
                  border: '1px solid rgba(255,214,0,0.2)',
                  fontSize: '0.72rem', color: '#ffd600', textAlign: 'center',
                }}>
                  ⚠ Tawk.to not configured. Set VITE_TAWK_PROPERTY_ID in .env to enable live chat.
                </div>
              )}

              <div style={{ textAlign: 'center', marginTop: 12, fontSize: '0.7rem', color: '#4a3570' }}>
                Powered by Tawk.to · Your data is shared with the support agent
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
