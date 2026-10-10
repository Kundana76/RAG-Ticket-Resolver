# -*- coding: utf-8 -*-
"""
Conversation Memory — Challenge 14 (Agentic Search) pattern.

Stores full ticket conversation context using Valkey JSON:
  JSON.SET conversation:{sessionId} $ '{...}'
  EXPIRE conversation:{sessionId} 1800

Key pattern from HACKATHON.md:
  conversation:{sessionId}

Each conversation tracks:
  - turns (user messages + agent responses)
  - context (intent, category, confidence)
  - resolution history
  - recommended KB articles
"""
import json
from datetime import datetime
from valkey_config import get_client, K
from copilot.valkey_json import json_set, json_get

CONV_TTL = 86400   # 24 hours (hackathon: 1800s for search sessions, 24h for tickets)


class ConversationMemory:
    def __init__(self):
        self.vk = get_client()

    # ── Create ───────────────────────────────────────────────

    def create_conversation(self, ticket_id: str, ticket_text: str,
                            category: str = None) -> dict:
        """
        Initialise a conversation document.
        JSON.SET conversation:{ticket_id} $ '{...}'
        """
        doc = {
            "ticket_id": ticket_id,
            "ticket_text": ticket_text,
            "category": category,
            "status": "open",
            "confidence_score": None,
            "resolution": None,
            "recommendations": [],
            "turns": [
                {
                    "role": "user",
                    "content": ticket_text,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
            "context": {
                "intent": "support_request",
                "category": category,
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        key = K.conversation(ticket_id)
        json_set(key, doc, ttl=CONV_TTL)
        return doc

    # ── Update ───────────────────────────────────────────────

    def add_agent_turn(self, ticket_id: str, content: str,
                       action: str = None, search_params: dict = None) -> None:
        """Append an agent response turn to the conversation."""
        doc = json_get(K.conversation(ticket_id))
        if not doc:
            return
        turn = {
            "role": "agent",
            "content": content,
            "action": action,
            "searchParams": search_params,
            "timestamp": datetime.utcnow().isoformat(),
        }
        doc.setdefault("turns", []).append(turn)
        doc["updated_at"] = datetime.utcnow().isoformat()
        json_set(K.conversation(ticket_id), doc, ttl=CONV_TTL)

    def store_resolution(self, ticket_id: str, resolution: dict) -> None:
        doc = json_get(K.conversation(ticket_id))
        if not doc:
            return
        doc["resolution"] = resolution
        doc["status"] = resolution.get("action", "resolved")
        doc["confidence_score"] = resolution.get("confidence_score")
        doc["updated_at"] = datetime.utcnow().isoformat()
        json_set(K.conversation(ticket_id), doc, ttl=CONV_TTL)

    def store_recommendations(self, ticket_id: str, recs: list) -> None:
        doc = json_get(K.conversation(ticket_id))
        if not doc:
            return
        doc["recommendations"] = recs
        doc["updated_at"] = datetime.utcnow().isoformat()
        json_set(K.conversation(ticket_id), doc, ttl=CONV_TTL)

    # ── Read ─────────────────────────────────────────────────

    def get_conversation(self, ticket_id: str) -> dict | None:
        return json_get(K.conversation(ticket_id))

    def get_recent_conversations(self, limit: int = 20) -> list:
        """Scan for recent conversation keys."""
        convs = []
        cursor = 0
        try:
            while True:
                cursor, keys = self.vk.scan(
                    cursor, match="conversation:*", count=200
                )
                for key in keys:
                    doc = json_get(key)
                    if doc:
                        convs.append(doc)
                if cursor == 0 or len(convs) >= limit:
                    break
        except Exception:
            pass
        convs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return convs[:limit]

    def get_stats(self) -> dict:
        convs = self.get_recent_conversations(limit=500)
        total = len(convs)
        if total == 0:
            return {"total": 0, "auto_resolved": 0, "escalated": 0,
                    "draft_response": 0, "open": 0,
                    "auto_resolution_rate": 0, "escalation_rate": 0}
        auto  = sum(1 for c in convs if c.get("status") == "auto_resolved")
        esc   = sum(1 for c in convs if c.get("status") == "escalated")
        draft = sum(1 for c in convs if c.get("status") == "draft_response")
        return {
            "total": total,
            "auto_resolved": auto,
            "escalated": esc,
            "draft_response": draft,
            "open": total - auto - esc - draft,
            "auto_resolution_rate": round(auto / total * 100, 1),
            "escalation_rate": round(esc / total * 100, 1),
        }
