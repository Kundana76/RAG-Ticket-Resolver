from copilot.resolution_engine import ResolutionEngine

RECS = [{"article_title": "Payment Failed Guide", "score": 0.9}]


def test_tiers_without_llm(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    e = ResolutionEngine()
    e._ready = False
    assert e.determine_action(0.9, "x", RECS)["action"] == "auto_resolved"
    assert e.determine_action(0.6, "x", RECS)["action"] == "draft_response"
    assert e.determine_action(0.1, "x", RECS)["action"] == "escalated"
