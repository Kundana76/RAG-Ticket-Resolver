"""
Pub/Sub Notifier - Real-time event notifications via Valkey Pub/Sub.

Publishes events when:
- Ticket is auto-resolved
- Ticket is escalated
- Incident spike detected
- KB article performance drops

Subscribers (Slack, dashboard, etc.) can listen to these channels.
"""
import json
from datetime import datetime
from valkey_config import get_valkey_client

# Pub/Sub Channels
CHANNELS = {
    "ticket_resolved": "copilot:resolved",
    "ticket_escalated": "copilot:escalated",
    "incident_spike": "copilot:spike",
    "kb_alert": "copilot:kb_alert",
}


class PubSubNotifier:
    def __init__(self):
        self.vk = get_valkey_client()

    def notify_resolution(self, ticket_id: str, action: str, confidence: float):
        """Publish ticket resolution event."""
        channel = CHANNELS["ticket_resolved"] if action == "auto_resolved" else CHANNELS["ticket_escalated"]
        message = json.dumps({
            "event": "ticket_processed",
            "ticket_id": ticket_id,
            "action": action,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.vk.publish(channel, message)

    def notify_spike(self, category: str, count: int):
        """Publish incident spike alert."""
        message = json.dumps({
            "event": "incident_spike",
            "category": category,
            "count": count,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.vk.publish(CHANNELS["incident_spike"], message)

    def notify_kb_alert(self, article: str, metric: str, value: float):
        """Publish KB performance alert."""
        message = json.dumps({
            "event": "kb_performance_alert",
            "article": article,
            "metric": metric,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.vk.publish(CHANNELS["kb_alert"], message)

    def subscribe(self, channel_key: str):
        """Subscribe to a notification channel (for listeners)."""
        pubsub = self.vk.pubsub()
        pubsub.subscribe(CHANNELS.get(channel_key, channel_key))
        return pubsub
