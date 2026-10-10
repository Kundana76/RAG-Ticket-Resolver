interface Props { action: string }

export function ActionBadge({ action }: Props) {
  if (action === 'auto_resolved') return <span className="badge-resolved">✓ AUTO-RESOLVED</span>
  if (action === 'escalated')     return <span className="badge-escalated">⚠ ESCALATED</span>
  return <span className="badge-draft">✎ DRAFT</span>
}
