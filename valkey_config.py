# -*- coding: utf-8 -*-
"""
Valkey Configuration
====================
Connects to valkey/valkey-bundle:9-alpine which includes all modules:
  - Valkey JSON  (JSON.SET / JSON.GET)
  - Valkey Search (FT.CREATE / FT.SEARCH)
  - Valkey Bloom  (BF.ADD / BF.EXISTS)
  - Valkey Geo    (GEOADD / GEOSEARCH)

Falls back to fakeredis for local dev when Docker is not running.

Prerequisites (from hackathon README):
  docker pull valkey/valkey-bundle:9-alpine
  docker run -d --name valkey -p 6379:6379 valkey/valkey-bundle:9-alpine

Connection:
  VALKEY_URL=redis://localhost:6379   (env var, hackathon convention)
"""
import os
import redis
from dotenv import load_dotenv

load_dotenv()

# Hackathon convention: VALKEY_URL=redis://localhost:6379
_url = os.getenv("VALKEY_URL", "redis://localhost:6379")
VALKEY_HOST = os.getenv("VALKEY_HOST", "localhost")
VALKEY_PORT = int(os.getenv("VALKEY_PORT", 6379))
VALKEY_PASSWORD = os.getenv("VALKEY_PASSWORD", None)

# ── Singleton state ──────────────────────────────────────────
_fake_server = None
_use_fake: bool | None = None


def _check_connection() -> bool:
    """Return True if real Valkey is reachable, False otherwise."""
    global _use_fake
    if _use_fake is not None:
        return not _use_fake
    try:
        r = redis.Redis(
            host=VALKEY_HOST, port=VALKEY_PORT,
            password=VALKEY_PASSWORD,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        r.ping()
        r.close()
        _use_fake = False
        print("[Valkey] ✓ Connected to valkey-bundle at "
              f"{VALKEY_HOST}:{VALKEY_PORT}")
    except Exception:
        _use_fake = True
        print("[Valkey] ⚠ No server found — using fakeredis (in-memory demo mode)")
    return not _use_fake


def _fake_srv():
    global _fake_server
    if _fake_server is None:
        import fakeredis
        _fake_server = fakeredis.FakeServer()
    return _fake_server


def get_client(decode: bool = True) -> redis.Redis:
    """Return a Valkey client (real or fake)."""
    _check_connection()
    if _use_fake:
        import fakeredis
        return fakeredis.FakeRedis(server=_fake_srv(), decode_responses=decode)
    return redis.Redis(
        host=VALKEY_HOST, port=VALKEY_PORT,
        password=VALKEY_PASSWORD,
        decode_responses=decode,
    )


# ── Hackathon key-naming convention ─────────────────────────
# Primary entities: key IS the entity ID  (ticket:uuid, session:uuid …)
# Derived data:     {purpose}:{entityId}  (cart:user:uuid, trending:global:1h …)

class K:
    """Centralised key builders — matches HACKATHON.md naming exactly."""

    # ── Tickets (our domain) ─────────────────────────────────
    @staticmethod
    def ticket(tid: str) -> str:
        return tid                          # "ticket:uuid" IS the key

    @staticmethod
    def session(token: str) -> str:
        return f"session:{token}"

    # ── Trending (Challenge 4) ───────────────────────────────
    TRENDING_GLOBAL_1H  = "trending:global:1h"
    TRENDING_GLOBAL_24H = "trending:global:24h"

    @staticmethod
    def trending_cat(cat: str, window: str) -> str:
        return f"trending:category:{cat}:{window}"

    # ── Analytics (Challenge 8) ──────────────────────────────
    @staticmethod
    def metric_orders(minute_ts: int) -> str:
        return f"metrics:orders:count:{minute_ts}"

    @staticmethod
    def metric_hourly(hour_ts: int) -> str:
        return f"metrics:revenue:{hour_ts}"

    @staticmethod
    def metric_latency(minute_ts: int) -> str:
        return f"metrics:api_latency:{minute_ts}"

    @staticmethod
    def active_users(date: str, hour: str) -> str:
        return f"active_users:{date}:{hour}"

    METRICS_GAUGES   = "metrics:gauges"
    METRICS_COUNTERS = "metrics:counters"

    # ── Escalation queue ─────────────────────────────────────
    ESCALATION_QUEUE = "escalation:queue"

    @staticmethod
    def escalation(tid: str) -> str:
        return f"escalation:ticket:{tid}"

    # ── Streams ──────────────────────────────────────────────
    STREAM_EVENTS = "stream:ticket:events"

    # ── Rate limiting (Challenge 12) ─────────────────────────
    @staticmethod
    def ratelimit(user_id: str, endpoint: str, window: int) -> str:
        return f"ratelimit:{user_id}:{endpoint}:{window}"

    # ── Recommendations / co-purchase (Challenge 13) ─────────
    @staticmethod
    def user_history(user_id: str) -> str:
        return f"user_history:{user_id}"

    @staticmethod
    def user_affinity(user_id: str) -> str:
        return f"user_affinity:{user_id}"

    # ── Agentic search conversation (Challenge 14) ───────────
    @staticmethod
    def conversation(session_id: str) -> str:
        return f"conversation:{session_id}"

    @staticmethod
    def agent_cache(query_hash: str) -> str:
        return f"agent_cache:{query_hash}"
