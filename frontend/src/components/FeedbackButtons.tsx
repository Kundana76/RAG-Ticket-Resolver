import { useState } from 'react'
import { ThumbsUp, ThumbsDown } from 'lucide-react'
import { api } from '../services/api'

interface Props {
  ticketId: string
  articleTitle: string
}

/** "Was this helpful?" for one recommended article. Re-clicking the other thumb changes the vote. */
export function FeedbackButtons({ ticketId, articleTitle }: Props) {
  const [vote, setVote] = useState<boolean | null>(null)
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState(false)

  const send = async (helpful: boolean) => {
    if (busy || vote === helpful) return
    setBusy(true); setFailed(false)
    try {
      await api.sendFeedback(ticketId, articleTitle, helpful)
      setVote(helpful)
    } catch {
      setFailed(true)
    } finally {
      setBusy(false)
    }
  }

  const btn = (active: boolean, color: string) => ({
    background: active ? `${color}22` : 'transparent',
    border: `1px solid ${active ? color : 'rgba(123,47,190,0.3)'}`,
    color: active ? color : '#9575cd',
    borderRadius: 6, padding: '4px 7px', cursor: busy ? 'wait' : 'pointer',
    display: 'flex', alignItems: 'center',
  } as React.CSSProperties)

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
      {failed && <span style={{ fontSize: '0.68rem', color: '#ff6b6b' }}>not saved</span>}
      {vote !== null && !failed && (
        <span style={{ fontSize: '0.68rem', color: '#9575cd' }}>thanks</span>
      )}
      <button type="button" title="This helped" aria-label="This helped"
        style={btn(vote === true, '#00e676')} onClick={() => send(true)}>
        <ThumbsUp size={13} />
      </button>
      <button type="button" title="This didn't help" aria-label="This didn't help"
        style={btn(vote === false, '#ff6b6b')} onClick={() => send(false)}>
        <ThumbsDown size={13} />
      </button>
    </div>
  )
}
