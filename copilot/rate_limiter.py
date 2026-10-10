# -*- coding: utf-8 -*-
"""
Rate Limiter — Challenge 12 (Rate Limiting).

Implements sliding-window rate limiting using Valkey Sorted Sets.
Returns X-RateLimit-* headers as per hackathon spec.

Key pattern:
  ratelimit:{userId}:{endpoint}:{window_start}

Config (from HACKATHON.md):
  /api/copilot/process  → authenticated: 30/min, anonymous: 10/min
  /api/trending         → authenticated: 60/min, anonymous: 30/min
  /metrics              → unlimited
"""
import time
import uuid
from valkey_config import get_client, K

# Endpoint rate limits: (anonymous_per_min, authenticated_per_min)
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/copilot/process":   (10, 30),
    "/recommend":         (20, 60),
    "/trending":          (30, 60),
    "/analytics/live":    (30, 60),
    "/escalation/queue":  (10, 30),
    "/demo/batch":        (5,  20),
    "/auth/login":        (8,  8),
    "/feedback":          (30, 60),
    "/webhooks/ticket":   (60, 120),
    "default":            (20, 60),
}

WINDOW_SECONDS = 60


class RateLimiter:
    def __init__(self):
        self.vk = get_client()

    def check(self, user_id: str, endpoint: str,
              authenticated: bool = False) -> dict:
        """
        Sliding-window rate limit check.

        Returns:
          {
            "allowed": bool,
            "limit": int,
            "remaining": int,
            "reset": int,          # Unix timestamp
            "retry_after": int,    # seconds (only when blocked)
          }
        """
        anon_limit, auth_limit = RATE_LIMITS.get(
            endpoint, RATE_LIMITS["default"]
        )
        limit = auth_limit if authenticated else anon_limit

        now    = time.time()
        window = now - WINDOW_SECONDS
        key    = K.ratelimit(user_id, endpoint, int(now // WINDOW_SECONDS))

        try:
            # Sliding window log
            req_id = str(uuid.uuid4())
            pipe = self.vk.pipeline()
            pipe.zadd(key, {req_id: now})
            pipe.zremrangebyscore(key, 0, window)
            pipe.zcard(key)
            pipe.expire(key, WINDOW_SECONDS * 2)
            results = pipe.execute()
            count = results[2]
        except Exception:
            # If Valkey is unavailable, allow the request
            return {"allowed": True, "limit": limit,
                    "remaining": limit, "reset": int(now) + WINDOW_SECONDS}

        reset_ts = int(now) + WINDOW_SECONDS
        if count > limit:
            return {
                "allowed":     False,
                "limit":       limit,
                "remaining":   0,
                "reset":       reset_ts,
                "retry_after": WINDOW_SECONDS,
            }

        return {
            "allowed":   True,
            "limit":     limit,
            "remaining": max(0, limit - count),
            "reset":     reset_ts,
        }
