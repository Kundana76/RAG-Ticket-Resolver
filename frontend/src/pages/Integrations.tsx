import { useState } from 'react'
import { usePolling } from '../hooks/usePolling'
import { api, errorMessage } from '../services/api'
import type { IntegrationStatus } from '../services/api'

const code: React.CSSProperties = {
  background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(123,47,190,0.25)', borderRadius: 8,
  padding: '10px 12px', fontSize: '0.75rem', color: '#d1c4e9', overflowX: 'auto', whiteSpace: 'pre',
  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', margin: '8px 0 0',
}

function Pill({ on }: { on: boolean }) {
  return (
    <span style={{
      fontSize: '0.7rem', fontWeight: 700, padding: '2px 10px', borderRadius: 20,
      color: on ? '#00e676' : '#9575cd',
      border: `1px solid ${on ? 'rgba(0,230,118,0.35)' : 'rgba(149,117,205,0.35)'}`,
    }}>
      {on ? 'ON' : 'NOT SET UP'}
    </span>
  )
}

function Card({ title, on, children }: { title: string; on: boolean; children: React.ReactNode }) {
  return (
    <div className="glass-card" style={{ padding: 20, marginBottom: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <div style={{ fontWeight: 700, color: '#ede7f6' }}>{title}</div>
        <Pill on={on} />
      </div>
      <div style={{ fontSize: '0.82rem', color: '#b39ddb', lineHeight: 1.6 }}>{children}</div>
    </div>
  )
}

export function Integrations() {
  const [status, setStatus] = useState<IntegrationStatus | null>(null)
  const [polling, setPolling] = useState(false)
  const [pollMsg, setPollMsg] = useState('')

  usePolling(async () => {
    try { setStatus(await api.getIntegrations()) } catch { /* shows loading state */ }
  }, 10000)

  const pollNow = async () => {
    setPolling(true); setPollMsg('')
    try {
      const r = await api.pollEmail()
      setPollMsg(`Checked inbox: ${r.processed} new ticket${r.processed === 1 ? '' : 's'}, ${r.skipped} skipped` +
        (r.errors?.length ? `, ${r.errors.length} failed (will retry)` : ''))
      setStatus(await api.getIntegrations())
    } catch (e) {
      setPollMsg(errorMessage(e, 'Inbox check failed'))
    } finally {
      setPolling(false)
    }
  }

  const origin = typeof window !== 'undefined' ? window.location.origin : ''

  return (
    <div style={{ padding: 28, maxWidth: 760 }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ede7f6', marginBottom: 4 }}>Integrations</h1>
      <p style={{ color: '#9575cd', marginBottom: 22, fontSize: '0.9rem' }}>
        Ways tickets get in, and where alerts go out. Secrets live in <code>.env</code> on the server, never here.
      </p>

      {!status ? (
        <div style={{ color: '#6b5b8a', fontSize: '0.9rem' }}>Loading…</div>
      ) : (
        <>
          <Card title="Email to ticket" on={status.email.configured}>
            {status.email.configured ? (
              <>
                New emails in the connected inbox become tickets
                {status.email.poll_seconds > 0
                  ? `, checked every ${Math.max(30, status.email.poll_seconds)}s.`
                  : '. Automatic checking is off (EMAIL_POLL_SECONDS=0), so use the button.'}
                {' '}Auto-reply is {status.email.auto_reply ? 'on' : 'off'}.
                <div style={{ marginTop: 12 }}>
                  <button className="btn-primary" onClick={pollNow} disabled={polling}>
                    {polling ? 'Checking…' : 'Check inbox now'}
                  </button>
                  {pollMsg && <span style={{ marginLeft: 12, color: '#d1c4e9' }}>{pollMsg}</span>}
                </div>
                {status.email.last_poll?.at && (
                  <div style={{ marginTop: 8, fontSize: '0.75rem', color: '#6b5b8a' }}>
                    Last check: {new Date(status.email.last_poll.at + 'Z').toLocaleString()}
                    {status.email.last_poll.errors?.length ? ` — ${status.email.last_poll.errors[0]}` : ''}
                  </div>
                )}
              </>
            ) : (
              <>
                Use a Gmail address with an App Password, then add these to <code>.env</code> and restart:
                <pre style={code}>{`IMAP_HOST=imap.gmail.com
IMAP_USER=you@gmail.com
IMAP_PASSWORD=<16-character app password>
EMAIL_POLL_SECONDS=60
# EMAIL_AUTO_REPLY=true   (optional: replies only when a ticket is auto-resolved)`}</pre>
              </>
            )}
          </Card>

          <Card title="Webhook" on={status.webhook.enabled}>
            {status.webhook.enabled ? (
              <>
                Send tickets from Zendesk, Freshdesk, Zapier, n8n or any form tool:
                <pre style={code}>{`curl -X POST ${origin}/api${status.webhook.path} \\
  -H "X-Webhook-Secret: $WEBHOOK_SECRET" \\
  -H "Content-Type: application/json" \\
  -d '{"subject":"Charged twice","description":"Billed two times this month","source":"zendesk"}'`}</pre>
              </>
            ) : (
              <>Set <code>WEBHOOK_SECRET</code> in <code>.env</code> (any long random string) and restart to turn this on.</>
            )}
          </Card>

          <Card title="Slack alerts" on={status.slack.enabled}>
            {status.slack.enabled
              ? 'Escalated tickets post to your Slack channel the moment they are escalated.'
              : <>Set <code>SLACK_WEBHOOK_URL</code> in <code>.env</code> to get an alert for every escalation.</>}
          </Card>
        </>
      )}
    </div>
  )
}
