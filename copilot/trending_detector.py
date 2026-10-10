# -*- coding: utf-8 -*-
"""
Trending Incident Detector — Challenge 4 (Trending Products pattern).

Uses Valkey Sorted Sets with weighted scoring:
  view       → +1
  escalated  → +3
  auto_resolved → +5   (treated as "purchase" equivalent)

Time windows: 1h and 24h with auto-expiry.
Key pattern (from HACKATHON.md):
  trending:global:1h
  trending:global:24h
  trending:category:{category}:1h
"""
import time
from datetime import datetime
from valkey_config import get_client, K

# Weighted scores (mirrors Challenge 4 spec)
WEIGHTS = {
    "view":          1,
    "draft_response": 3,   # add-to-cart equivalent
    "auto_resolved":  5,   # purchase equivalent
    "escalated":      3,
}

SPIKE_THRESHOLD = 5   # incidents in window = spike
WINDOW_1H  = 3600
WINDOW_24H = 86400

# Incident categories with keyword mapping
CATEGORY_KEYWORDS = {
    "payment_failure":   ["payment", "charged", "transaction", "declined", "deducted"],
    "login_issue":       ["login", "password", "sign in", "locked out", "authentication"],
    "api_error":         ["api", "error", "timeout", "500", "connection", "server"],
    "delivery_complaint":["delivery", "shipping", "not received", "delayed", "tracking"],
    "billing_dispute":   ["billing", "invoice", "overcharged", "double charge"],
    "account_locked":    ["locked", "suspended", "disabled", "blocked", "access denied"],
    "refund_request":    ["refund", "money back", "return", "cancel order"],
    "service_outage":    ["down", "outage", "not working", "unavailable", "maintenance"],
}


class TrendingDetector:
    def __init__(self):
        self.vk = get_client()

    # ── Category detection ───────────────────────────────────

    def detect_category(self, text: str) -> str:
        text_lower = text.lower()
        best, best_score = "other", 0
        for cat, kws in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in kws if kw in text_lower)
            if score > best_score:
                best, best_score = cat, score
        return best

    # ── Record an incident ───────────────────────────────────

    def record_incident(self, category: str, ticket_id: str,
                        action: str = "view") -> None:
        """
        Record a ticket event.
        Mirrors HACKATHON.md Challenge 4:
          ZINCRBY trending:global:1h  {weight} {category}
          ZINCRBY trending:global:24h {weight} {category}
          ZINCRBY trending:category:{cat}:1h {weight} {category}
        """
        weight = WEIGHTS.get(action, 1)
        try:
            self.vk.zincrby(K.TRENDING_GLOBAL_1H,  weight, category)
            self.vk.zincrby(K.TRENDING_GLOBAL_24H, weight, category)
            self.vk.zincrby(K.trending_cat(category, "1h"), weight, ticket_id)
            # Auto-expire hourly bucket
            self.vk.expire(K.TRENDING_GLOBAL_1H, WINDOW_1H)
            self.vk.expire(K.trending_cat(category, "1h"), WINDOW_1H)
        except Exception:
            pass

    # ── Query trending ───────────────────────────────────────

    def get_trending(self, window: str = "1h", top_n: int = 8) -> list:
        """
        Get top trending categories.
        ZREVRANGE trending:global:1h 0 {top_n-1} WITHSCORES
        """
        key = K.TRENDING_GLOBAL_1H if window == "1h" else K.TRENDING_GLOBAL_24H
        try:
            raw = self.vk.zrevrange(key, 0, top_n - 1, withscores=True)
            return [
                {
                    "category": cat,
                    "score": int(score),
                    "is_spike": int(score) >= SPIKE_THRESHOLD,
                    "window": window,
                }
                for cat, score in raw
            ]
        except Exception:
            return []

    def get_all_scores(self) -> dict:
        """All-time scores from 24h window."""
        try:
            raw = self.vk.zrevrange(K.TRENDING_GLOBAL_24H, 0, -1, withscores=True)
            return {cat: int(score) for cat, score in raw}
        except Exception:
            return {}

    def get_spike_alerts(self) -> list:
        return [t for t in self.get_trending() if t["is_spike"]]

    def reset_scores(self) -> None:
        try:
            self.vk.delete(K.TRENDING_GLOBAL_1H, K.TRENDING_GLOBAL_24H)
        except Exception:
            pass
