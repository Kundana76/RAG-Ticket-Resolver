# -*- coding: utf-8 -*-
"""
AI Support Copilot — FastAPI Backend
=====================================
Build Beyond Limits Hackathon | Powered by Valkey

Implements (from HACKATHON.md):
  Challenge 4  — Trending Incidents (Sorted Sets)
  Challenge 8  — Analytics + Prometheus /metrics
  Challenge 12 — Rate Limiting (Sliding Window)
  Challenge 13 — Recommendations (co-purchase pattern)
  Challenge 14 — Agentic Search (Conversation Memory)

Prerequisites:
  docker pull valkey/valkey-bundle:9-alpine
  docker run -d --name valkey -p 6379:6379 valkey/valkey-bundle:9-alpine

Connection:
  VALKEY_URL=redis://localhost:6379
"""
import os
import re
import json
import time
import hmac
import hashlib
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from copilot.id_utils import create_id
from copilot.trending_detector import TrendingDetector
from copilot.conversation_memory import ConversationMemory
from copilot.analytics import AnalyticsEngine
from copilot.escalation import EscalationManager
from copilot.rate_limiter import RateLimiter
from copilot.config import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CORS_ORIGINS
from copilot.feedback import FeedbackStore
from copilot.auth import AuthManager, issue_token, optional_user, require_agent, require_admin, auth_required, TOKEN_TTL
from integrations.slack_alerts import notify_escalation
from integrations import email_ingest

# ── Background email poller ──────────────────────────────────

_last_poll: dict = {}
_poll_stop = threading.Event()


def _poll_inbox() -> dict:
    """One pass over the inbox: every new email becomes a ticket."""
    def handle(item: dict) -> dict:
        res = _run_pipeline(item["text"], None, None, None, source="email")
        if res["action"] == "auto_resolved":
            email_ingest.send_reply(item, res)
        return res

    summary = email_ingest.poll(handle)
    _last_poll.update(summary, at=datetime.utcnow().isoformat())
    return summary


def _poll_loop(interval: int) -> None:
    while not _poll_stop.is_set():
        try:
            _poll_inbox()
        except Exception as e:
            _last_poll.update(errors=[f"{type(e).__name__}: {e}"], at=datetime.utcnow().isoformat())
        _poll_stop.wait(interval)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    AuthManager().bootstrap_from_env()
    interval = int(os.getenv("EMAIL_POLL_SECONDS", "0") or 0)
    if interval > 0 and email_ingest.configured():
        _poll_stop.clear()
        threading.Thread(target=_poll_loop, args=(max(interval, 30),), daemon=True).start()
        print(f"[email] polling inbox every {max(interval, 30)}s")
    yield
    _poll_stop.set()


# ── App ──────────────────────────────────────────────────────

app = FastAPI(
    lifespan=lifespan,
    title="AI Support Copilot",
    description=(
        "Valkey-powered intelligent support platform. "
        "Build Beyond Limits Hackathon — React Hyderabad."
    ),
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singletons ───────────────────────────────────────────────

trending    = TrendingDetector()
memory      = ConversationMemory()
analytics   = AnalyticsEngine()
escalation  = EscalationManager()
rate_limiter = RateLimiter()
feedback_store = FeedbackStore()
auth_mgr = AuthManager()

# ── ML resources (lazy) ──────────────────────────────────────

_ml = None

def _load_ml():
    global _ml
    if _ml is not None:
        return _ml
    try:
        import pickle, faiss
        import pandas as pd
        from sentence_transformers import SentenceTransformer
        with open("models/embed_model.pkl", "rb") as f:
            info = pickle.load(f)
        model    = SentenceTransformer(info["model_name"])
        articles = pd.read_pickle("models/articles_meta.pkl")
        index    = faiss.read_index("models/article_index.faiss")
        _ml = (model, articles, index)
        print("[ML] Loaded FAISS + SentenceTransformer")
    except Exception as e:
        print(f"[ML] Unavailable ({e}) — using mock KB articles")
        _ml = (None, None, None)
    return _ml

# ── Resolution engine (lazy) ─────────────────────────────────

_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        try:
            from copilot.resolution_engine import ResolutionEngine
            _engine = ResolutionEngine()
        except Exception:
            _engine = None
    return _engine

# ── Helpers ──────────────────────────────────────────────────

MOCK_KB = [
    "Payment Troubleshooting Guide",
    "Account Recovery Steps",
    "Refund Policy & Process",
    "Login Issues Resolution",
    "API Error Codes Reference",
    "Delivery Tracking Help",
    "Billing Dispute Resolution",
    "Service Status Page Guide",
    "Password Reset Instructions",
    "Order Cancellation Policy",
]

def _search_kb(text: str, top_k: int = 3) -> list:
    """Semantic KB search via FAISS, or mock data."""
    model, articles, index = _load_ml()
    if model is None:
        import random, hashlib
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % 10000
        random.seed(seed)
        selected = random.sample(MOCK_KB, min(top_k, len(MOCK_KB)))
        scores   = sorted([random.uniform(0.45, 0.95) for _ in selected], reverse=True)
        return [
            {"rank": i+1, "article_title": t, "score": round(s, 3)}
            for i, (t, s) in enumerate(zip(selected, scores))
        ]
    import faiss as _faiss
    emb = model.encode([text], convert_to_numpy=True)
    _faiss.normalize_L2(emb)
    D, I = index.search(emb, top_k)
    return [
        {"rank": i+1, "article_title": articles.iloc[idx]["title"],
         "article_id": str(articles.iloc[idx].get("kb_id", "")),
         "category": str(articles.iloc[idx].get("category", "")),
         "snippet": str(articles.iloc[idx].get("content", ""))[:300],
         "score": float(D[0][i])}
        for i, idx in enumerate(I[0])
    ]

def _get_recommendations(text: str, top_k: int = 3) -> list:
    """KB search, then nudge scores with 'was this helpful?' feedback (small, bounded)."""
    recs = _search_kb(text, top_k)
    adj = feedback_store.adjustments([r["article_title"] for r in recs])
    if any(adj.values()):
        for r in recs:
            delta = adj.get(r["article_title"], 0.0)
            r["raw_score"] = r["score"]
            r["feedback_adjustment"] = delta
            r["score"] = round(min(1.0, max(0.0, r["score"] + delta)), 4)
        recs.sort(key=lambda r: r["score"], reverse=True)
        for i, r in enumerate(recs):
            r["rank"] = i + 1
    return recs


def _resolve(confidence: float, text: str, recs: list) -> dict:
    """Run resolution engine or fallback."""
    engine = _get_engine()
    if engine:
        res = engine.determine_action(confidence, text, recs)
    else:
        if confidence >= CONFIDENCE_HIGH:
            res = {
                "action": "auto_resolved", "confidence_tier": "high",
                "resolution": f"Resolved via: {recs[0]['article_title'] if recs else 'N/A'}",
                "source_article": recs[0]["article_title"] if recs else "N/A",
                "timestamp": datetime.utcnow().isoformat(),
            }
        elif confidence >= CONFIDENCE_MEDIUM:
            res = {
                "action": "draft_response", "confidence_tier": "medium",
                "draft": "Suggested: " + ", ".join(r["article_title"] for r in recs[:2]) + ". [VERIFY]",
                "recommendations": recs[:3],
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            res = {
                "action": "escalated", "confidence_tier": "low",
                "summary": {
                    "issue_summary": text[:120],
                    "attempted_fixes": "KB semantic search — low confidence",
                    "probable_root_cause": "Requires human investigation",
                    "priority": "high",
                },
                "recommendations": recs[:3],
                "timestamp": datetime.utcnow().isoformat(),
            }
    res["confidence_score"] = confidence
    return res

def _rate_limit_headers(result: dict) -> dict:
    return {
        "X-RateLimit-Limit":     str(result["limit"]),
        "X-RateLimit-Remaining": str(result["remaining"]),
        "X-RateLimit-Reset":     str(result["reset"]),
    }

# ── Pydantic models ──────────────────────────────────────────

class TicketInput(BaseModel):
    ticket_id:   Optional[str]   = None
    ticket_text: str
    category:    Optional[str]   = None
    confidence:  Optional[float] = None

class AgentMessage(BaseModel):
    session_id:  Optional[str] = None
    message:     str
    user_id:     Optional[str] = None

class EscalationClaim(BaseModel):
    agent_name: Optional[str] = None   # ignored: the signed-in agent is used

class EscalationResolve(BaseModel):
    ticket_id:       str
    resolution_note: str

class DemoTicketBatch(BaseModel):
    tickets: list[dict]

class FeedbackIn(BaseModel):
    ticket_id:     str = Field(min_length=1, max_length=120)
    article_title: str = Field(min_length=1, max_length=200)
    helpful:       bool
    comment:       Optional[str] = Field(default=None, max_length=500)

class LoginIn(BaseModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=256)

class RegisterIn(BaseModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=256)
    role:     Optional[str] = "agent"

class WebhookTicket(BaseModel):
    """Generic inbound ticket. Accepts ticket_text, or subject + description."""
    ticket_text:    Optional[str] = Field(default=None, max_length=8000)
    subject:        Optional[str] = Field(default=None, max_length=300)
    description:    Optional[str] = Field(default=None, max_length=8000)
    ticket_id:      Optional[str] = None
    category:       Optional[str] = None
    customer_email: Optional[str] = Field(default=None, max_length=200)
    source:         Optional[str] = Field(default="webhook", max_length=40)

# ════════════════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
def root():
    return {
        "service":     "AI Support Copilot",
        "version":     "2.0.0",
        "status":      "running",
        "powered_by":  "valkey/valkey-bundle:9-alpine",
        "hackathon":   "Build Beyond Limits — React Hyderabad",
        "challenges":  ["4-Trending", "8-Analytics", "12-RateLimit",
                        "13-Recommendations", "14-AgenticSearch"],
        "docs":        "/docs",
        "metrics":     "/metrics",
    }

# ── Challenge 8: Prometheus metrics ─────────────────────────

@app.get("/metrics", response_class=PlainTextResponse, tags=["Analytics"])
def prometheus_metrics():
    """Prometheus exposition format — Challenge 8."""
    return analytics.prometheus_metrics()

# ── Core: Process ticket ─────────────────────────────────────

def _check_rate(request: Request, endpoint: str, authenticated: bool = False) -> dict:
    """Per-client-IP sliding window. Raises 429 when exceeded."""
    user_id = request.client.host if request.client else "anonymous"
    rl = rate_limiter.check(user_id, endpoint, authenticated=authenticated)
    if not rl["allowed"]:
        raise HTTPException(
            status_code=429,
            detail={"error": "rate_limit_exceeded",
                    "message": f"Too many requests. Retry in {rl['retry_after']}s.",
                    "retry_after": rl["retry_after"]},
            headers=_rate_limit_headers(rl),
        )
    return rl


def _run_pipeline(text: str, ticket_id: Optional[str], category: Optional[str],
                  confidence: Optional[float], source: str = "api") -> dict:
    """
    The whole ticket flow, shared by the web form, webhook and email intake:
      1. ID + category  2. KB recommendations  3. confidence-based resolution
      4. trending  5. conversation memory  6. analytics  7. escalation queue
    """
    t0 = time.time()

    ticket_id = ticket_id or create_id("ticket")
    category = category or trending.detect_category(text)

    recs = _get_recommendations(text)
    confidence = confidence if confidence is not None else (
        recs[0]["score"] if recs else 0.5
    )

    resolution = _resolve(confidence, text, recs)

    trending.record_incident(category, ticket_id, action=resolution["action"])

    memory.create_conversation(ticket_id, text, category)
    memory.store_recommendations(ticket_id, recs)
    memory.store_resolution(ticket_id, resolution)
    memory.add_agent_turn(
        ticket_id,
        content=resolution.get("resolution") or resolution.get("draft") or "Escalated",
        action=resolution["action"],
    )

    latency_ms = (time.time() - t0) * 1000
    analytics.record_ticket(ticket_id, category, resolution["action"], confidence, latency_ms)
    for rec in recs:
        analytics.record_kb_hit(rec["article_title"], rec["score"])

    if resolution["action"] == "escalated":
        doc = escalation.escalate_ticket(
            ticket_id=ticket_id,
            ticket_text=text,
            category=category,
            recommendations=recs,
            escalation_summary=resolution.get("summary", {}),
            confidence=confidence,
        )
        notify_escalation(doc)

    return {
        "ticket_id":       ticket_id,
        "category":        category,
        "confidence":      confidence,
        "action":          resolution["action"],
        "resolution":      resolution,
        "recommendations": recs,
        "source":          source,
        "timestamp":       datetime.utcnow().isoformat(),
        "latency_ms":      round(latency_ms, 2),
    }


@app.post("/copilot/process", tags=["Copilot"])
def process_ticket(ticket: TicketInput, request: Request):
    """Run a ticket through the full pipeline (see _run_pipeline)."""
    rl = _check_rate(request, "/copilot/process", authenticated=bool(ticket.ticket_id))
    result = _run_pipeline(ticket.ticket_text, ticket.ticket_id, ticket.category, ticket.confidence)
    return Response(content=json.dumps(result), media_type="application/json",
                    headers=_rate_limit_headers(rl))


# ── Feedback loop ────────────────────────────────────────────

@app.post("/feedback", tags=["Feedback"])
def submit_feedback(body: FeedbackIn, request: Request, user: Optional[dict] = Depends(optional_user)):
    """'Was this helpful?' vote on a recommended article. One vote per ticket+article (re-voting changes it)."""
    _check_rate(request, "/feedback")
    return feedback_store.record(body.ticket_id, body.article_title, body.helpful,
                                 body.comment or "", user["username"] if user else None)

@app.get("/feedback/stats", tags=["Feedback"])
def feedback_stats():
    return feedback_store.stats()

# ── Auth ─────────────────────────────────────────────────────

@app.get("/auth/status", tags=["Auth"])
def auth_status():
    """Public: lets the UI decide between 'sign in' and 'create the first admin'."""
    return {"auth_required": auth_required(), "has_users": auth_mgr.user_count() > 0}

@app.post("/auth/login", tags=["Auth"])
def login(body: LoginIn, request: Request):
    _check_rate(request, "/auth/login")
    user = auth_mgr.authenticate(body.username, body.password)
    if not user:
        raise HTTPException(401, "Wrong username or password")
    return {"token": issue_token(user["username"], user["role"]),
            "user": user, "expires_in": TOKEN_TTL}

@app.post("/auth/register", tags=["Auth"])
def register(body: RegisterIn, request: Request, user: Optional[dict] = Depends(optional_user)):
    """First account is open and becomes admin. After that only an admin can add users."""
    _check_rate(request, "/auth/login")
    first = auth_mgr.user_count() == 0
    if not first and not (user and user["role"] == "admin"):
        raise HTTPException(403, "Only an admin can create accounts")
    try:
        created = auth_mgr.create_user(body.username, body.password,
                                       "admin" if first else (body.role or "agent"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    if first:
        return {"user": created, "token": issue_token(created["username"], created["role"]),
                "expires_in": TOKEN_TTL}
    return {"user": created}

@app.get("/auth/me", tags=["Auth"])
def me(user: dict = Depends(require_agent)):
    return user

@app.get("/auth/users", tags=["Auth"])
def list_users(_: dict = Depends(require_admin)):
    return auth_mgr.list_users()

# ── Inbound intake: webhook + email ──────────────────────────

_TICKET_ID_RE = re.compile(r"^[A-Za-z0-9:_.\-]{1,80}$")

@app.post("/webhooks/ticket", tags=["Integrations"])
def webhook_ticket(payload: WebhookTicket, request: Request,
                   x_webhook_secret: Optional[str] = Header(default=None)):
    """
    Inbound ticket from any helpdesk or form tool (Zendesk, Freshdesk, Typeform, n8n, Zapier...).
    Send header  X-Webhook-Secret: <WEBHOOK_SECRET>  and a JSON body.
    Disabled until WEBHOOK_SECRET is set.
    """
    secret = os.getenv("WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(503, "Webhook intake is disabled (WEBHOOK_SECRET is not set)")
    if not hmac.compare_digest((x_webhook_secret or "").encode(), secret.encode()):
        raise HTTPException(401, "Bad webhook secret")
    rl = _check_rate(request, "/webhooks/ticket", authenticated=True)

    text = (payload.ticket_text or "").strip() or \
        f"{(payload.subject or '').strip()}\n\n{(payload.description or '').strip()}".strip()
    if len(text) < 5:
        raise HTTPException(400, "Provide ticket_text, or subject and description")
    if payload.ticket_id and not _TICKET_ID_RE.match(payload.ticket_id):
        raise HTTPException(400, "ticket_id may only contain letters, digits and : _ . -")

    result = _run_pipeline(text, payload.ticket_id, payload.category, None,
                           source=(payload.source or "webhook"))
    return Response(content=json.dumps(result), media_type="application/json",
                    headers=_rate_limit_headers(rl))

@app.post("/integrations/email/poll", tags=["Integrations"])
def poll_email_now(_: dict = Depends(require_agent)):
    """Check the inbox right now and turn new emails into tickets."""
    if not email_ingest.configured():
        raise HTTPException(503, "Email intake is not configured (set IMAP_HOST, IMAP_USER, IMAP_PASSWORD)")
    try:
        return _poll_inbox()
    except Exception as e:
        raise HTTPException(502, f"Inbox check failed: {type(e).__name__}")

@app.get("/integrations/status", tags=["Integrations"])
def integrations_status(_: dict = Depends(require_agent)):
    """Which integrations are switched on. Booleans only — never returns secrets."""
    return {
        "email": {
            "configured": email_ingest.configured(),
            "auto_reply": email_ingest.auto_reply_enabled(),
            "poll_seconds": int(os.getenv("EMAIL_POLL_SECONDS", "0") or 0),
            "last_poll": _last_poll or None,
        },
        "webhook": {"enabled": bool(os.getenv("WEBHOOK_SECRET")), "path": "/webhooks/ticket"},
        "slack": {"enabled": bool(os.getenv("SLACK_WEBHOOK_URL"))},
    }

# ── Challenge 14: Agentic Search ─────────────────────────────

@app.post("/agent/search", tags=["Agentic Search"])
def agent_search(msg: AgentMessage):
    """
    Natural language ticket search with conversation memory.
    Maintains context across turns (Challenge 14).
    """
    session_id = msg.session_id or create_id("session")

    # Check agent cache (avoid re-running expensive searches)
    from valkey_config import get_client, K
    cache_key = K.agent_cache(
        hashlib.md5(msg.message.encode()).hexdigest()
    )
    vk = get_client()
    cached = vk.get(cache_key)
    if cached:
        import json
        result = json.loads(cached)
        result["session_id"] = session_id
        result["cached"] = True
        return result

    # Get or create conversation
    conv = memory.get_conversation(session_id)
    if not conv:
        conv = memory.create_conversation(session_id, msg.message)

    # Detect category and get recommendations
    category = trending.detect_category(msg.message)
    recs     = _get_recommendations(msg.message, top_k=5)
    confidence = recs[0]["score"] if recs else 0.5

    # Build agent response
    resolution = _resolve(confidence, msg.message, recs)
    follow_up  = _build_follow_up(category, confidence)

    result = {
        "session_id":  session_id,
        "response":    resolution.get("resolution") or resolution.get("draft") or
                       "I've escalated this to a human agent with full context.",
        "action":      resolution["action"],
        "confidence":  confidence,
        "results":     [
            {
                "article_title": r["article_title"],
                "score":         r["score"],
                "reason":        f"Matched with {r['score']*100:.0f}% confidence",
            }
            for r in recs[:3]
        ],
        "follow_up":   follow_up,
        "context": {
            "intent":    "support_request",
            "category":  category,
            "turns":     len(conv.get("turns", [])) + 1,
        },
        "cached": False,
    }

    # Store agent turn in conversation memory
    memory.add_agent_turn(session_id, result["response"],
                          action=resolution["action"],
                          search_params={"category": category, "confidence": confidence})

    # Cache result for 5 minutes
    import json
    vk.set(cache_key, json.dumps(result), ex=300)

    # Record analytics
    analytics.record_ticket(session_id, category, resolution["action"], confidence)
    trending.record_incident(category, session_id, action=resolution["action"])

    return result

@app.get("/agent/conversation/{session_id}", tags=["Agentic Search"])
def get_conversation(session_id: str):
    """Get full conversation history for a session (Challenge 14)."""
    conv = memory.get_conversation(session_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv

# ── Challenge 4: Trending ────────────────────────────────────

@app.get("/trending", tags=["Trending"])
def get_trending(window: str = "1h"):
    """
    Trending incident categories.
    ZREVRANGE trending:global:{window} 0 9 WITHSCORES
    """
    return {
        "trending":     trending.get_trending(window=window),
        "all_scores":   trending.get_all_scores(),
        "spike_alerts": trending.get_spike_alerts(),
        "window":       window,
    }

@app.post("/events/view", tags=["Trending"])
def record_view(ticket: TicketInput):
    """Record a ticket view event (Challenge 4)."""
    cat = ticket.category or trending.detect_category(ticket.ticket_text)
    trending.record_incident(cat, ticket.ticket_id or "anon", action="view")
    return {"status": "recorded", "category": cat}

# ── Challenge 8: Analytics ───────────────────────────────────

@app.get("/analytics/live", tags=["Analytics"])
def live_analytics():
    """Real-time dashboard metrics."""
    return analytics.get_live_metrics()

@app.get("/analytics/trend", tags=["Analytics"])
def hourly_trend(hours: int = 12):
    """Hourly ticket volume (last N hours)."""
    return analytics.get_hourly_trend(hours=hours)

@app.get("/analytics/kb-performance", tags=["Analytics"])
def kb_performance():
    """KB article impression and score metrics."""
    return analytics.get_kb_performance(top_n=10)

@app.get("/analytics/activity-feed", tags=["Analytics"])
def activity_feed(count: int = 20):
    """Live activity stream from Valkey Streams."""
    return analytics.get_activity_feed(count=count)

@app.get("/analytics/dashboard", tags=["Analytics"])
def analytics_dashboard():
    """Combined dashboard data endpoint."""
    return {
        "live":          analytics.get_live_metrics(),
        "hourly_trend":  analytics.get_hourly_trend(hours=12),
        "kb_top10":      analytics.get_kb_performance(top_n=10),
        "trending":      trending.get_trending(),
        "spike_alerts":  trending.get_spike_alerts(),
        "escalation_queue_length": escalation.get_queue_length(),
    }

# ── Escalation queue ─────────────────────────────────────────

@app.get("/escalation/queue", tags=["Escalation"])
def get_escalation_queue(_: dict = Depends(require_agent)):
    return {
        "queue": escalation.get_queue(),
        "stats": escalation.get_escalation_stats(),
    }

@app.post("/escalation/claim", tags=["Escalation"])
def claim_escalation(claim: EscalationClaim, user: dict = Depends(require_agent)):
    result = escalation.claim_escalation(user["username"])
    if not result:
        raise HTTPException(404, "No pending escalations")
    return result

@app.post("/escalation/resolve", tags=["Escalation"])
def resolve_escalation(body: EscalationResolve, user: dict = Depends(require_agent)):
    result = escalation.resolve_escalation(body.ticket_id, body.resolution_note, resolved_by=user["username"])
    if not result:
        raise HTTPException(404, "Escalation not found")
    return result

# ── Conversations ────────────────────────────────────────────

@app.get("/conversations/recent", tags=["Conversations"])
def recent_conversations(_: dict = Depends(require_agent)):
    return memory.get_recent_conversations(limit=20)

@app.get("/conversation/{ticket_id}", tags=["Conversations"])
def get_ticket_conversation(ticket_id: str, _: dict = Depends(require_agent)):
    conv = memory.get_conversation(ticket_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv

# ── Backward-compatible recommend endpoint ───────────────────

@app.post("/recommend", tags=["Recommendations"])
def recommend(ticket: TicketInput):
    """Backward-compatible endpoint from original project."""
    recs = _get_recommendations(ticket.ticket_text)
    return {
        "ticket_id":       ticket.ticket_id,
        "ticket_text":     ticket.ticket_text,
        "recommendations": recs,
    }

# ── Demo utilities ───────────────────────────────────────────

@app.get("/demo/sample-tickets", tags=["Demo"])
def sample_tickets():
    return [
        {"ticket_id": create_id("ticket"), "ticket_text": "I was charged twice for my subscription payment",    "category": "billing_dispute"},
        {"ticket_id": create_id("ticket"), "ticket_text": "Cannot login to my account, password reset not working", "category": "login_issue"},
        {"ticket_id": create_id("ticket"), "ticket_text": "API returning 500 errors on all endpoints since morning", "category": "api_error"},
        {"ticket_id": create_id("ticket"), "ticket_text": "My package shows delivered but I never received it",  "category": "delivery_complaint"},
        {"ticket_id": create_id("ticket"), "ticket_text": "Payment declined even though my card has sufficient balance", "category": "payment_failure"},
        {"ticket_id": create_id("ticket"), "ticket_text": "App crashes every time I try to open settings",       "category": "api_error"},
        {"ticket_id": create_id("ticket"), "ticket_text": "Need refund for order cancelled 3 days ago",          "category": "refund_request"},
        {"ticket_id": create_id("ticket"), "ticket_text": "Account locked after too many login attempts",        "category": "account_locked"},
        {"ticket_id": create_id("ticket"), "ticket_text": "Delivery delayed by 2 weeks, no tracking update",    "category": "delivery_complaint"},
        {"ticket_id": create_id("ticket"), "ticket_text": "Service completely down, cannot access any features", "category": "service_outage"},
        {"ticket_id": create_id("ticket"), "ticket_text": "Payment gateway timeout during checkout",             "category": "payment_failure"},
        {"ticket_id": create_id("ticket"), "ticket_text": "Wrong item delivered, need exchange",                 "category": "delivery_complaint"},
    ]

@app.post("/demo/batch", tags=["Demo"])
def demo_batch(batch: DemoTicketBatch, request: Request):
    """Batch process tickets for demo population."""
    results = []
    for t in batch.tickets:
        ticket = TicketInput(
            ticket_id=t.get("ticket_id"),
            ticket_text=t.get("ticket_text", ""),
            category=t.get("category"),
            confidence=t.get("confidence"),
        )
        result = process_ticket(ticket, request)
        import json
        results.append(json.loads(result.body))
    return {"processed": len(results), "results": results}

@app.post("/demo/reset", tags=["Demo"])
def demo_reset(_: dict = Depends(require_admin)):
    """Reset all Valkey data for a fresh demo."""
    trending.reset_scores()
    analytics.reset_analytics()
    escalation.clear_queue()
    return {"status": "reset", "message": "All Valkey data cleared"}

# ── Helpers ──────────────────────────────────────────────────

def _build_follow_up(category: str, confidence: float) -> str:
    if confidence >= CONFIDENCE_HIGH:
        return "Is there anything else I can help you with?"
    if category == "payment_failure":
        return "Would you like me to check your recent transactions or connect you with billing?"
    if category == "login_issue":
        return "Should I guide you through account recovery or escalate to the security team?"
    if category == "delivery_complaint":
        return "Would you like real-time tracking information or to file a missing item report?"
    return "Would you like me to refine the search or escalate to a human agent?"

import hashlib
