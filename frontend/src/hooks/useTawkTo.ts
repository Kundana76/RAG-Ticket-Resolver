/**
 * Tawk.to Integration Hook
 * 
 * Loads the Tawk.to widget and provides controls to:
 * - Show/hide the widget (hidden by default)
 * - Open chat on escalation
 * - Pass ticket context as visitor attributes
 * 
 * Setup:
 *   1. Go to https://dashboard.tawk.to
 *   2. Create a property (or use existing)
 *   3. Go to Administration → Chat Widget
 *   4. Copy Property ID from embed URL: https://embed.tawk.to/{propertyId}/{widgetId}
 *   5. Set in frontend/.env:
 *        VITE_TAWK_PROPERTY_ID=your_property_id
 *        VITE_TAWK_WIDGET_ID=default  (or your widget ID)
 */
import { useEffect, useRef, useCallback } from 'react'

const TAWK_PROPERTY_ID = import.meta.env.VITE_TAWK_PROPERTY_ID || ''
const TAWK_WIDGET_ID = import.meta.env.VITE_TAWK_WIDGET_ID || 'default'

declare global {
  interface Window {
    Tawk_API?: {
      maximize: () => void
      minimize: () => void
      hideWidget: () => void
      showWidget: () => void
      toggle: () => void
      setAttributes: (attrs: Record<string, string>, callback?: (error: any) => void) => void
      addEvent: (event: string, metadata?: Record<string, string>, callback?: (error: any) => void) => void
      onLoad?: () => void
    }
    Tawk_LoadStart?: Date
  }
}

export interface EscalationContext {
  ticketId: string
  ticketText: string
  category: string
  confidence: number
  urgency: string
  aiResolution: string
  kbArticles: string[]
}

export function useTawkTo() {
  const loadedRef = useRef(false)
  const readyRef = useRef(false)

  const isConfigured = Boolean(TAWK_PROPERTY_ID && TAWK_PROPERTY_ID.length > 5)

  // Load Tawk.to script once
  useEffect(() => {
    if (loadedRef.current || !isConfigured) return
    loadedRef.current = true

    window.Tawk_LoadStart = new Date()
    window.Tawk_API = window.Tawk_API || {} as any
    window.Tawk_API!.onLoad = () => {
      readyRef.current = true
      // Keep widget always visible and maximized
      window.Tawk_API?.showWidget()
    }

    const script = document.createElement('script')
    script.async = true
    script.src = `https://embed.tawk.to/${TAWK_PROPERTY_ID}/${TAWK_WIDGET_ID}`
    script.charset = 'UTF-8'
    script.setAttribute('crossorigin', '*')
    document.head.appendChild(script)
  }, [isConfigured])

  const openChat = useCallback(() => {
    if (!isConfigured) {
      console.log('[Tawk.to] Not configured — set VITE_TAWK_PROPERTY_ID in frontend/.env')
      return
    }
    if (window.Tawk_API && readyRef.current) {
      window.Tawk_API.showWidget()
      window.Tawk_API.maximize()
    }
  }, [isConfigured])

  const hideChat = useCallback(() => {
    if (window.Tawk_API && readyRef.current) {
      window.Tawk_API.minimize()
      window.Tawk_API.hideWidget()
    }
  }, [])

  const setEscalationContext = useCallback((ctx: EscalationContext) => {
    if (window.Tawk_API && readyRef.current) {
      window.Tawk_API.setAttributes({
        'ticket-id': ctx.ticketId,
        'category': ctx.category,
        'confidence': `${(ctx.confidence * 100).toFixed(0)}%`,
        'urgency': ctx.urgency,
        'issue-summary': ctx.ticketText.slice(0, 200),
      })
      window.Tawk_API.addEvent('ai-escalation', {
        'ticket-id': ctx.ticketId,
        'category': ctx.category,
        'confidence': `${(ctx.confidence * 100).toFixed(0)}%`,
        'issue': ctx.ticketText.slice(0, 150),
        'kb-articles': ctx.kbArticles.join(', ').slice(0, 200),
      })
    }
  }, [])

  const escalate = useCallback((ctx: EscalationContext) => {
    setEscalationContext(ctx)
    openChat()
  }, [setEscalationContext, openChat])

  return {
    openChat,
    hideChat,
    escalate,
    setEscalationContext,
    isConfigured,
  }
}
