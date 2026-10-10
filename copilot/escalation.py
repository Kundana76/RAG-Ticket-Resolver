# -*- coding: utf-8 -*-
"""
Escalation Manager — Intelligent escalation queue.

Uses Valkey List as a FIFO queue (LPUSH / RPOP) and
Valkey JSON for individual escalation documents.

Key pattern:
  escalation:queue          → List (FIFO queue)
  escalation:ticket:{id}    → JSON document
"""
import json
from datetime import datetime
from valkey_config import get_client, K
from copilot.valkey_json import json_set, json_get


class EscalationManager:
    def __init__(self):
        self.vk = get_client()

    def escalate_ticket(self, ticket_id: str, ticket_text: str,
                        category: str, recommendations: list,
                        escalation_summary: dict, confidence: float) -> dict:
        doc = {
            "ticket_id":        ticket_id,
            "ticket_text":      ticket_text,
            "category":         category,
            "confidence_score": confidence,
            "issue_summary":    escalation_summary.get("issue_summary", ticket_text[:100]),
            "attempted_fixes":  escalation_summary.get("attempted_fixes", "KB search performed"),
            "probable_root_cause": escalation_summary.get("probable_root_cause", "Unknown"),
            "priority":         escalation_summary.get("priority", "medium"),
            "recommended_articles": [
                {"title": r.get("article_title", ""), "score": r.get("score", 0)}
                for r in recommendations[:3]
            ],
            "status":     "pending",
            "created_at": datetime.utcnow().isoformat(),
            "assigned_to": None,
        }
        try:
            self.vk.lpush(K.ESCALATION_QUEUE, json.dumps(doc))
        except Exception:
            pass
        json_set(K.escalation(ticket_id), doc, ttl=86400)
        return doc

    def get_queue(self, limit: int = 20) -> list:
        try:
            raw = self.vk.lrange(K.ESCALATION_QUEUE, 0, limit - 1)
            return [json.loads(r) for r in raw]
        except Exception:
            return []

    def get_queue_length(self) -> int:
        try:
            return self.vk.llen(K.ESCALATION_QUEUE)
        except Exception:
            return 0

    def claim_escalation(self, agent_name: str) -> dict | None:
        try:
            raw = self.vk.rpop(K.ESCALATION_QUEUE)
        except Exception:
            return None
        if not raw:
            return None
        doc = json.loads(raw)
        doc["status"]     = "claimed"
        doc["assigned_to"] = agent_name
        doc["claimed_at"] = datetime.utcnow().isoformat()
        json_set(f"escalation:claimed:{doc['ticket_id']}", doc, ttl=86400)
        return doc

    def resolve_escalation(self, ticket_id: str, note: str, resolved_by: str | None = None) -> dict | None:
        doc = json_get(f"escalation:claimed:{ticket_id}")
        if not doc:
            return None
        doc["status"]          = "resolved_by_agent"
        doc["resolution_note"] = note
        doc["resolved_by"]     = resolved_by
        doc["resolved_at"]     = datetime.utcnow().isoformat()
        json_set(f"escalation:claimed:{ticket_id}", doc, ttl=86400)
        return doc

    def get_escalation_stats(self) -> dict:
        return {
            "pending":   self.get_queue_length(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def clear_queue(self) -> None:
        try:
            self.vk.delete(K.ESCALATION_QUEUE)
        except Exception:
            pass
