# -*- coding: utf-8 -*-
"""
Resolution Engine — Confidence-based ticket resolution.

Thresholds:
  >= 0.85  → auto_resolved   (high confidence)
  >= 0.50  → draft_response  (medium confidence)
  <  0.50  → escalated       (low confidence)

Uses Groq LLM when GROQ_API_KEY is set; falls back to
rule-based responses otherwise.
"""
import os
import json
from datetime import datetime

from copilot.config import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM


class ResolutionEngine:
    def __init__(self):
        self._client = None
        self._model  = "llama-3.1-8b-instant"
        self._ready  = False
        try:
            from groq import Groq
            from dotenv import load_dotenv
            load_dotenv()
            key = os.getenv("GROQ_API_KEY")
            if key:
                self._client = Groq(api_key=key)
                self._ready  = True
        except Exception:
            pass

    # ── Public API ───────────────────────────────────────────

    def determine_action(self, confidence: float, ticket_text: str,
                         recommendations: list) -> dict:
        if confidence >= CONFIDENCE_HIGH:
            return self._auto_resolve(ticket_text, recommendations)
        elif confidence >= CONFIDENCE_MEDIUM:
            return self._draft_response(ticket_text, recommendations)
        else:
            return self._escalate(ticket_text, recommendations)

    # ── Resolution paths ─────────────────────────────────────

    def _auto_resolve(self, text: str, recs: list) -> dict:
        top = recs[0] if recs else {}
        msg = self._llm_resolve(text, top) if self._ready else (
            f"Your issue has been resolved. Please refer to: "
            f"{top.get('article_title', 'our support documentation')}."
        )
        return {
            "action":           "auto_resolved",
            "confidence_tier":  "high",
            "resolution":       msg,
            "source_article":   top.get("article_title", "N/A"),
            "timestamp":        datetime.utcnow().isoformat(),
        }

    def _draft_response(self, text: str, recs: list) -> dict:
        draft = self._llm_draft(text, recs) if self._ready else (
            f"Thank you for contacting support. Based on your issue, "
            f"we suggest reviewing: "
            + ", ".join(r.get("article_title", "") for r in recs[:2])
            + ". [VERIFY] Please confirm if this resolves your issue."
        )
        return {
            "action":          "draft_response",
            "confidence_tier": "medium",
            "draft":           draft,
            "recommendations": recs[:3],
            "timestamp":       datetime.utcnow().isoformat(),
        }

    def _escalate(self, text: str, recs: list) -> dict:
        summary = self._llm_escalation_summary(text, recs) if self._ready else {
            "issue_summary":       text[:120],
            "attempted_fixes":     "Semantic KB search — low confidence matches only",
            "probable_root_cause": "Requires human investigation",
            "priority":            "high",
        }
        return {
            "action":          "escalated",
            "confidence_tier": "low",
            "summary":         summary,
            "recommendations": recs[:3],
            "timestamp":       datetime.utcnow().isoformat(),
        }

    # ── LLM helpers ──────────────────────────────────────────

    def _llm_resolve(self, text: str, article: dict) -> str:
        prompt = (
            f"You are a customer support AI. Write a brief, friendly resolution "
            f"(2-3 sentences) for this ticket using the KB article.\n\n"
            f"Ticket: {text}\nKB Article: {article.get('article_title', 'General Support')}"
        )
        try:
            r = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=200,
            )
            return r.choices[0].message.content.strip()
        except Exception:
            return f"Resolved via: {article.get('article_title', 'N/A')}"

    def _llm_draft(self, text: str, recs: list) -> str:
        articles = ", ".join(r.get("article_title", "") for r in recs[:3])
        prompt = (
            f"Draft a support response for agent review (3-4 sentences). "
            f"Mark uncertain parts with [VERIFY].\n\n"
            f"Ticket: {text}\nRelated articles: {articles}"
        )
        try:
            r = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4, max_tokens=300,
            )
            return r.choices[0].message.content.strip()
        except Exception:
            return f"Draft based on: {articles}. Please review."

    def _llm_escalation_summary(self, text: str, recs: list) -> dict:
        articles = ", ".join(r.get("article_title", "") for r in recs[:3])
        prompt = (
            f"Create an escalation summary JSON with keys: "
            f"issue_summary, attempted_fixes, probable_root_cause, priority.\n\n"
            f"Ticket: {text}\nKB matches: {articles}\n\nRespond ONLY in JSON."
        )
        try:
            r = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2, max_tokens=300,
            )
            raw = r.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].replace("json", "").strip()
            return json.loads(raw)
        except Exception:
            return {
                "issue_summary":       text[:120],
                "attempted_fixes":     f"KB search: {articles}",
                "probable_root_cause": "Unknown — human review needed",
                "priority":            "high",
            }
