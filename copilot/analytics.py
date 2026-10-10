# -*- coding: utf-8 -*-
"""
Analytics Engine — Challenge 8 (Analytics with Prometheus).

Uses Valkey data structures exactly as specified in HACKATHON.md:

  # Orders counter (per-minute bucket)
  INCR metrics:orders:count:{minute_ts}
  EXPIRE metrics:orders:count:{minute_ts} 86400

  # Active users (HyperLogLog)
  PFADD active_users:{date}:{hour} {userId}
  PFCOUNT active_users:{date}:{hour}

  # Gauge metrics
  HSET metrics:gauges  escalation_rate 0.20

  # Latency histogram
  HINCRBY metrics:latency_histogram:{minute_ts} "le_50" 1

  # Event stream (capped at 1000)
  XADD stream:ticket:events * ...

  # KB article impressions
  ZINCRBY analytics:kb:impressions 1 {article}

Exposes /metrics in Prometheus exposition format.
"""
import time
from datetime import datetime, timedelta
from valkey_config import get_client, K

_MINUTE = 60
_HOUR   = 3600
_DAY    = 86400


class AnalyticsEngine:
    def __init__(self):
        self.vk = get_client()

    # ── Record a processed ticket ────────────────────────────

    def record_ticket(self, ticket_id: str, category: str,
                      action: str, confidence: float,
                      latency_ms: float = 0) -> None:
        now      = int(time.time())
        minute   = (now // _MINUTE) * _MINUTE
        hour     = (now // _HOUR)   * _HOUR
        today    = datetime.utcnow().strftime("%Y-%m-%d")
        hour_str = datetime.utcnow().strftime("%H")

        try:
            # Orders counter (per-minute)
            mk = K.metric_orders(minute)
            self.vk.incr(mk)
            self.vk.expire(mk, _DAY)

            # Revenue / action counter (per-hour)
            hk = K.metric_hourly(hour)
            self.vk.hincrby(hk, "total", 1)
            self.vk.hincrby(hk, f"action:{action}", 1)
            self.vk.hincrby(hk, f"category:{category}", 1)
            self.vk.expire(hk, _DAY * 7)

            # Active users (HyperLogLog)
            self.vk.pfadd(K.active_users(today, hour_str), ticket_id)

            # Gauge metrics
            stats = self.get_live_metrics()
            self.vk.hset(K.METRICS_GAUGES, mapping={
                "total_today":         stats.get("total_tickets_today", 0),
                "auto_resolution_rate": stats.get("auto_resolution_rate", 0),
                "escalation_rate":      stats.get("escalation_rate", 0),
            })

            # Latency histogram
            if latency_ms > 0:
                lk = K.metric_latency(minute)
                bucket = self._latency_bucket(latency_ms)
                self.vk.hincrby(lk, bucket, 1)
                self.vk.expire(lk, _DAY)

            # Event stream (XADD, capped at 1000)
            self.vk.xadd(K.STREAM_EVENTS, {
                "ticket_id":  ticket_id,
                "category":   category,
                "action":     action,
                "confidence": str(round(confidence, 3)),
                "timestamp":  datetime.utcnow().isoformat(),
            }, maxlen=1000)

        except Exception:
            pass

    def record_kb_hit(self, article: str, score: float) -> None:
        """Track KB article impressions (Sorted Set)."""
        try:
            self.vk.zincrby("analytics:kb:impressions", 1, article)
            self.vk.hincrbyfloat("analytics:kb:scores", article, score)
            self.vk.hincrby("analytics:kb:counts", article, 1)
        except Exception:
            pass

    # ── Live metrics ─────────────────────────────────────────

    def get_live_metrics(self) -> dict:
        now   = int(time.time())
        hour  = (now // _HOUR) * _HOUR
        today = datetime.utcnow().strftime("%Y-%m-%d")
        hour_str = datetime.utcnow().strftime("%H")

        try:
            hk   = K.metric_hourly(hour)
            data = self.vk.hgetall(hk)
            total = int(data.get("total", 0))
            auto  = int(data.get("action:auto_resolved", 0))
            esc   = int(data.get("action:escalated", 0))
            draft = int(data.get("action:draft_response", 0))

            # Unique active users via HyperLogLog
            active = self.vk.pfcount(K.active_users(today, hour_str))

            cats = {
                k.replace("category:", ""): int(v)
                for k, v in data.items()
                if k.startswith("category:")
            }

            return {
                "total_tickets_today":   total,
                "auto_resolved":         auto,
                "escalated":             esc,
                "draft_responses":       draft,
                "active_users":          active,
                "auto_resolution_rate":  round(auto / total * 100, 1) if total else 0,
                "escalation_rate":       round(esc  / total * 100, 1) if total else 0,
                "categories":            cats,
            }
        except Exception:
            return {
                "total_tickets_today": 0, "auto_resolved": 0,
                "escalated": 0, "draft_responses": 0,
                "active_users": 0, "auto_resolution_rate": 0,
                "escalation_rate": 0, "categories": {},
            }

    def get_hourly_trend(self, hours: int = 12) -> list:
        """Hourly ticket volume for the last N hours."""
        trend = []
        now = datetime.utcnow()
        for i in range(hours):
            dt  = now - timedelta(hours=i)
            hts = int(dt.replace(minute=0, second=0, microsecond=0).timestamp())
            hk  = K.metric_hourly(hts)
            try:
                data = self.vk.hgetall(hk)
            except Exception:
                data = {}
            trend.append({
                "hour":          dt.strftime("%H:00"),
                "total":         int(data.get("total", 0)),
                "auto_resolved": int(data.get("action:auto_resolved", 0)),
                "escalated":     int(data.get("action:escalated", 0)),
            })
        trend.reverse()
        return trend

    def get_kb_performance(self, top_n: int = 10) -> list:
        try:
            raw    = self.vk.zrevrange("analytics:kb:impressions", 0, top_n - 1, withscores=True)
            counts = self.vk.hgetall("analytics:kb:counts")
            scores = self.vk.hgetall("analytics:kb:scores")
        except Exception:
            return []

        results = []
        for article, imp in raw:
            cnt = int(counts.get(article, 1))
            avg = float(scores.get(article, 0)) / cnt if cnt else 0
            results.append({
                "article":     article,
                "impressions": int(imp),
                "avg_score":   round(avg, 3),
            })
        return results

    def get_activity_feed(self, count: int = 20) -> list:
        """Recent events from the Valkey Stream."""
        try:
            entries = self.vk.xrevrange(K.STREAM_EVENTS, count=count)
            return [
                {
                    "id":         eid,
                    "ticket_id":  d.get("ticket_id", ""),
                    "category":   d.get("category", ""),
                    "action":     d.get("action", ""),
                    "confidence": float(d.get("confidence", 0)),
                    "timestamp":  d.get("timestamp", ""),
                }
                for eid, d in entries
            ]
        except Exception:
            return []

    # ── Prometheus exposition format ─────────────────────────

    def prometheus_metrics(self) -> str:
        """
        /metrics endpoint — Prometheus exposition format.
        Challenge 8 acceptance criteria.
        """
        m = self.get_live_metrics()
        now = int(time.time())
        minute = (now // _MINUTE) * _MINUTE

        # Latency histogram
        try:
            lk   = K.metric_latency(minute)
            hist = self.vk.hgetall(lk)
        except Exception:
            hist = {}

        lines = [
            "# HELP tickets_total Total support tickets processed",
            "# TYPE tickets_total counter",
            f'tickets_total{{action="auto_resolved"}} {m["auto_resolved"]}',
            f'tickets_total{{action="escalated"}} {m["escalated"]}',
            f'tickets_total{{action="draft_response"}} {m["draft_responses"]}',
            "",
            "# HELP active_users_total Current unique active users (HyperLogLog)",
            "# TYPE active_users_total gauge",
            f'active_users_total {m["active_users"]}',
            "",
            "# HELP auto_resolution_rate Auto-resolution percentage",
            "# TYPE auto_resolution_rate gauge",
            f'auto_resolution_rate {m["auto_resolution_rate"]}',
            "",
            "# HELP escalation_rate Escalation percentage",
            "# TYPE escalation_rate gauge",
            f'escalation_rate {m["escalation_rate"]}',
            "",
            "# HELP ticket_latency_ms Ticket processing latency histogram",
            "# TYPE ticket_latency_ms histogram",
            f'ticket_latency_ms_bucket{{le="10"}}  {hist.get("le_10", 0)}',
            f'ticket_latency_ms_bucket{{le="50"}}  {hist.get("le_50", 0)}',
            f'ticket_latency_ms_bucket{{le="100"}} {hist.get("le_100", 0)}',
            f'ticket_latency_ms_bucket{{le="500"}} {hist.get("le_500", 0)}',
            f'ticket_latency_ms_bucket{{le="+Inf"}} {hist.get("le_inf", 0)}',
        ]

        # Per-category counters
        lines += ["", "# HELP tickets_by_category Tickets per incident category",
                  "# TYPE tickets_by_category counter"]
        for cat, cnt in m.get("categories", {}).items():
            lines.append(f'tickets_by_category{{category="{cat}"}} {cnt}')

        return "\n".join(lines) + "\n"

    # ── Helpers ──────────────────────────────────────────────

    def _latency_bucket(self, ms: float) -> str:
        if ms <= 10:   return "le_10"
        if ms <= 50:   return "le_50"
        if ms <= 100:  return "le_100"
        if ms <= 500:  return "le_500"
        return "le_inf"

    def reset_analytics(self) -> None:
        try:
            cursor = 0
            while True:
                cursor, keys = self.vk.scan(cursor, match="metrics:*", count=200)
                if keys:
                    self.vk.delete(*keys)
                if cursor == 0:
                    break
            self.vk.delete(K.STREAM_EVENTS, "analytics:kb:impressions",
                           "analytics:kb:scores", "analytics:kb:counts")
        except Exception:
            pass
