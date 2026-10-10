from email.message import EmailMessage

from integrations import email_ingest

HOOK = {"X-Webhook-Secret": "hook-secret"}


def test_webhook_rejects_bad_secret(client):
    r = client.post("/webhooks/ticket", json={"ticket_text": "hello there"},
                    headers={"X-Webhook-Secret": "wrong"})
    assert r.status_code == 401
    assert client.post("/webhooks/ticket", json={"ticket_text": "hello there"}).status_code == 401


def test_webhook_creates_ticket_from_subject_and_description(client):
    r = client.post("/webhooks/ticket", headers=HOOK, json={
        "subject": "Charged twice", "description": "I was billed two times this month",
        "source": "zendesk", "ticket_id": "zd-1001"})
    assert r.status_code == 200
    body = r.json()
    assert body["ticket_id"] == "zd-1001"
    assert body["source"] == "zendesk"
    assert body["action"] in ("auto_resolved", "draft_response", "escalated")


def test_webhook_validation(client):
    assert client.post("/webhooks/ticket", headers=HOOK, json={}).status_code == 400
    r = client.post("/webhooks/ticket", headers=HOOK,
                    json={"ticket_text": "hello there", "ticket_id": "bad id/with spaces"})
    assert r.status_code == 400


def test_webhook_disabled_without_secret(client, monkeypatch):
    monkeypatch.delenv("WEBHOOK_SECRET")
    assert client.post("/webhooks/ticket", headers=HOOK, json={"ticket_text": "hello there"}).status_code == 503


def test_integrations_status_requires_login_and_hides_secrets(client, admin_headers):
    assert client.get("/integrations/status").status_code == 401
    body = client.get("/integrations/status", headers=admin_headers).json()
    assert body["webhook"]["enabled"] is True
    assert "hook-secret" not in str(body)


def test_email_poll_503_when_unconfigured(client, admin_headers, monkeypatch):
    monkeypatch.delenv("IMAP_HOST", raising=False)
    assert client.post("/integrations/email/poll", headers=admin_headers).status_code == 503


# ── email parsing ───────────────────────────────────────────

def _raw(subject, body, **headers):
    m = EmailMessage()
    m["From"] = headers.pop("From", "Customer <cust@example.com>")
    m["To"] = "support@example.com"
    m["Subject"] = subject
    m["Message-ID"] = "<abc@example.com>"
    for k, v in headers.items():
        m[k.replace("_", "-")] = v
    m.set_content(body)
    return m.as_bytes()


def test_parse_normal_email_strips_quoted_reply():
    item = email_ingest.parse_message(_raw(
        "Cannot log in", "Password reset is not working.\n\nOn Mon, Jan 1, Support wrote:\n> old stuff"))
    assert item["sender"] == "cust@example.com"
    assert "Password reset is not working." in item["text"]
    assert "old stuff" not in item["text"]


def test_parse_skips_automated_mail():
    assert email_ingest.parse_message(_raw("Out of office", "I am away", Auto_Submitted="auto-replied")) is None
    assert email_ingest.parse_message(_raw("Newsletter", "buy now", Precedence="bulk")) is None
    assert email_ingest.parse_message(_raw("Alert", "disk full", From="no-reply@example.com")) is None


def test_auto_reply_is_off_by_default(monkeypatch):
    monkeypatch.delenv("EMAIL_AUTO_REPLY", raising=False)
    assert email_ingest.send_reply({"sender": "a@b.com"}, {"resolution": {}}) is False


# ── full poll loop against a fake IMAP server ───────────────

class _FakeImap:
    stored = []
    def __init__(self, *a, **k): pass
    def login(self, *a): return "OK", []
    def select(self, *a): return "OK", []
    def search(self, *a): return "OK", [b"1"]
    def fetch(self, num, spec):
        return "OK", [(b"1 (BODY[] {n})", _raw("Refund please", "I cancelled my order, where is my refund?"))]
    def store(self, num, op, flag): _FakeImap.stored.append((num, flag))
    def logout(self): pass


def test_poll_processes_once_and_dedupes(monkeypatch):
    from valkey_config import get_client
    get_client().delete(email_ingest.SEEN_KEY)
    monkeypatch.setattr(email_ingest.imaplib, "IMAP4_SSL", _FakeImap)
    for k, v in {"IMAP_HOST": "x", "IMAP_USER": "u", "IMAP_PASSWORD": "p"}.items():
        monkeypatch.setenv(k, v)
    seen = []
    handler = lambda item: seen.append(item["text"]) or {"ticket_id": f"t{len(seen)}"}

    first = email_ingest.poll(handler)
    assert first["processed"] == 1 and first["tickets"] == ["t1"]
    assert "Refund please" in seen[0]
    assert (b"1", "\\Seen") in _FakeImap.stored

    second = email_ingest.poll(handler)           # same Message-ID again
    assert second["processed"] == 0 and second["skipped"] == 1
    assert len(seen) == 1


def test_poll_failure_leaves_mail_unread(monkeypatch):
    from valkey_config import get_client
    get_client().delete(email_ingest.SEEN_KEY)
    _FakeImap.stored.clear()
    monkeypatch.setattr(email_ingest.imaplib, "IMAP4_SSL", _FakeImap)
    for k, v in {"IMAP_HOST": "x", "IMAP_USER": "u", "IMAP_PASSWORD": "p"}.items():
        monkeypatch.setenv(k, v)

    def boom(item): raise ValueError("engine down")
    out = email_ingest.poll(boom)
    assert out["processed"] == 0 and out["errors"]
    assert _FakeImap.stored == []                 # not marked read -> retried next poll
