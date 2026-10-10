# -*- coding: utf-8 -*-
"""
Feedback loop — "was this helpful?" votes on KB recommendations.

Votes are stored in Valkey and nudge future rankings: articles people keep
marking helpful drift up, articles marked unhelpful drift down. The nudge is
deliberately small (+/- MAX_SWING) and only kicks in after MIN_VOTES, so a
single click can never flip the routing decision on its own.

Keys:
  feedback:votes   hash   "<slug>:up" / "<slug>:down" -> counter
  feedback:titles  hash   "<slug>" -> article title
  feedback:cast    hash   "<ticket>|<slug>" -> "up" | "down"   (one vote per ticket+article)
  feedback:log     list   recent votes (JSON), capped
"""
import hashlib
import json
from datetime import datetime, timezone

from valkey_config import get_client

VOTES_KEY = "feedback:votes"
TITLES_KEY = "feedback:titles"
CAST_KEY = "feedback:cast"
LOG_KEY = "feedback:log"

MIN_VOTES = 3        # no ranking change until an article has this many votes
MAX_SWING = 0.10     # maximum score change (+/-) feedback can apply
FULL_WEIGHT_AT = 10  # votes needed before the full swing is applied
LOG_CAP = 200


def _slug(title: str) -> str:
    return hashlib.md5(title.strip().lower().encode()).hexdigest()[:12]


def compute_adjustment(up: int, down: int) -> float:
    """Score delta for an article given its vote counts."""
    n = up + down
    if n < MIN_VOTES:
        return 0.0
    ratio = (up - down) / n                      # -1 .. 1
    weight = min(1.0, n / FULL_WEIGHT_AT)        # ramps up with more votes
    return round(ratio * weight * MAX_SWING, 4)


class FeedbackStore:
    def __init__(self):
        self.vk = get_client()

    def record(self, ticket_id: str, article_title: str, helpful: bool,
               comment: str = "", user: str | None = None) -> dict:
        title = article_title.strip()[:200]
        slug = _slug(title)
        vote = "up" if helpful else "down"
        cast_key = f"{ticket_id}|{slug}"

        previous = self.vk.hget(CAST_KEY, cast_key)
        changed = previous != vote
        if changed:
            pipe = self.vk.pipeline()
            if previous in ("up", "down"):       # user changed their mind
                pipe.hincrby(VOTES_KEY, f"{slug}:{previous}", -1)
            pipe.hincrby(VOTES_KEY, f"{slug}:{vote}", 1)
            pipe.hset(CAST_KEY, cast_key, vote)
            pipe.hset(TITLES_KEY, slug, title)
            pipe.lpush(LOG_KEY, json.dumps({
                "ticket_id": ticket_id,
                "article_title": title,
                "helpful": helpful,
                "comment": (comment or "")[:500],
                "user": user,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }))
            pipe.ltrim(LOG_KEY, 0, LOG_CAP - 1)
            pipe.execute()

        up, down = self._counts(slug)
        return {
            "article_title": title,
            "helpful_votes": up,
            "unhelpful_votes": down,
            "adjustment": compute_adjustment(up, down),
            "changed": changed,
        }

    def _counts(self, slug: str) -> tuple[int, int]:
        up, down = self.vk.hmget(VOTES_KEY, f"{slug}:up", f"{slug}:down")
        return max(0, int(up or 0)), max(0, int(down or 0))

    def adjustments(self, titles: list[str]) -> dict[str, float]:
        """Map title -> score delta. Never raises (feedback is best-effort)."""
        try:
            out = {}
            for t in titles:
                up, down = self._counts(_slug(t))
                out[t] = compute_adjustment(up, down)
            return out
        except Exception:
            return {}

    def stats(self, limit: int = 20) -> dict:
        votes = self.vk.hgetall(VOTES_KEY)
        titles = self.vk.hgetall(TITLES_KEY)
        arts = []
        for slug, title in titles.items():
            up = max(0, int(votes.get(f"{slug}:up", 0)))
            down = max(0, int(votes.get(f"{slug}:down", 0)))
            if up + down == 0:
                continue
            arts.append({
                "article_title": title,
                "helpful": up,
                "unhelpful": down,
                "helpful_rate": round(up / (up + down), 3),
                "adjustment": compute_adjustment(up, down),
            })
        arts.sort(key=lambda a: (a["helpful"] + a["unhelpful"]), reverse=True)
        total_up = sum(a["helpful"] for a in arts)
        total_down = sum(a["unhelpful"] for a in arts)
        total = total_up + total_down
        recent = [json.loads(x) for x in self.vk.lrange(LOG_KEY, 0, 9)]
        return {
            "total_votes": total,
            "helpful_rate": round(total_up / total, 3) if total else None,
            "articles": arts[:limit],
            "recent": recent,
        }

    def reset(self) -> None:
        self.vk.delete(VOTES_KEY, TITLES_KEY, CAST_KEY, LOG_KEY)
