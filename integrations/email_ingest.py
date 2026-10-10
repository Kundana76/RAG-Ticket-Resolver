# -*- coding: utf-8 -*-
"""
Email-to-ticket intake (IMAP) with optional auto-reply (SMTP).

Works with Gmail: turn on 2-step verification, create an App Password
(https://myaccount.google.com/apppasswords) and use it as IMAP_PASSWORD.

Env:
  IMAP_HOST        e.g. imap.gmail.com
  IMAP_USER        mailbox address
  IMAP_PASSWORD    app password (never your normal password)
  IMAP_FOLDER      default INBOX
  EMAIL_POLL_SECONDS   >0 starts a background poller inside the API process
  EMAIL_AUTO_REPLY     "true" to email the customer when a ticket is auto-resolved
  SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD / SMTP_FROM
                   defaults: SMTP_HOST=smtp.gmail.com, SMTP_PORT=465,
                   SMTP_USER/SMTP_PASSWORD fall back to the IMAP ones

Safety:
  * Bulk / automated mail (Auto-Submitted, Precedence, no-reply, mailer-daemon) is skipped,
    so the bot can never get into a reply loop with another bot.
  * Each Message-ID is processed once (Valkey set), and a message is only marked
    read after it was handled successfully.
  * Auto-reply is OFF by default and only ever sent for auto-resolved tickets.
"""
import email
import imaplib
import os
import re
import smtplib
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr

from valkey_config import get_client

SEEN_KEY = "email:seen_ids"
MAX_BODY_CHARS = 4000

_SKIP_SENDERS = re.compile(r"(no-?reply|do-?not-?reply|mailer-daemon|postmaster)", re.I)
_QUOTE_CUTOFF = re.compile(r"^(on .+ wrote:|-{2,}\s*original message\s*-{2,}|from:\s.+@)", re.I)


def configured() -> bool:
    return bool(os.getenv("IMAP_HOST") and os.getenv("IMAP_USER") and os.getenv("IMAP_PASSWORD"))


def auto_reply_enabled() -> bool:
    return os.getenv("EMAIL_AUTO_REPLY", "false").strip().lower() in ("1", "true", "yes")


# ── parsing ─────────────────────────────────────────────────

def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", html)
    return re.sub(r"<[^>]+>", " ", html)


def _body_text(msg: email.message.Message) -> str:
    plain, html = None, None
    parts = msg.walk() if msg.is_multipart() else [msg]
    for part in parts:
        if part.get_content_disposition() == "attachment":
            continue
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        try:
            text = part.get_payload(decode=True).decode(
                part.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            continue
        if ctype == "text/plain" and plain is None:
            plain = text
        elif ctype == "text/html" and html is None:
            html = text
    return plain if plain is not None else _strip_html(html or "")


def clean_body(text: str) -> str:
    """Drop quoted replies and signatures-ish noise, collapse whitespace, cap length."""
    lines = []
    for line in text.replace("\r", "").split("\n"):
        stripped = line.strip()
        if _QUOTE_CUTOFF.match(stripped):
            break
        if stripped.startswith(">"):
            continue
        if stripped == "--":
            break
        lines.append(stripped)
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return out[:MAX_BODY_CHARS]


def is_automated(msg: email.message.Message) -> bool:
    if msg.get("Auto-Submitted", "no").strip().lower() != "no":
        return True
    if msg.get("Precedence", "").strip().lower() in ("bulk", "junk", "list", "auto_reply"):
        return True
    if msg.get("List-Id") or msg.get("X-Autoreply") or msg.get("X-Autorespond"):
        return True
    _, addr = parseaddr(msg.get("From", ""))
    return bool(_SKIP_SENDERS.search(addr))


def parse_message(raw: bytes) -> dict | None:
    """Return {message_id, sender, subject, text, ...} or None if it should be skipped."""
    msg = email.message_from_bytes(raw)
    if is_automated(msg):
        return None
    subject = _decode(msg.get("Subject")).strip()
    body = clean_body(_body_text(msg))
    text = f"{subject}\n\n{body}".strip()
    if len(text) < 5:
        return None
    return {
        "message_id": (msg.get("Message-ID") or "").strip(),
        "sender": parseaddr(msg.get("From", ""))[1],
        "subject": subject,
        "text": text,
    }


# ── polling ─────────────────────────────────────────────────

def poll(process_fn, limit: int = 20) -> dict:
    """
    Fetch unread mail and call process_fn(item) -> result dict for each.
    Returns {"fetched", "processed", "skipped", "tickets": [ids], "errors": [msg]}.
    """
    if not configured():
        raise RuntimeError("Email intake is not configured (set IMAP_HOST, IMAP_USER, IMAP_PASSWORD)")

    vk = get_client()
    summary = {"fetched": 0, "processed": 0, "skipped": 0, "tickets": [], "errors": []}

    conn = imaplib.IMAP4_SSL(os.environ["IMAP_HOST"], int(os.getenv("IMAP_PORT", 993)))
    try:
        conn.login(os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"])
        conn.select(os.getenv("IMAP_FOLDER", "INBOX"))
        status, data = conn.search(None, "UNSEEN")
        if status != "OK":
            raise RuntimeError("IMAP search failed")
        ids = data[0].split()[:limit]
        summary["fetched"] = len(ids)

        for num in ids:
            status, fetched = conn.fetch(num, "(BODY.PEEK[])")
            if status != "OK" or not fetched or not isinstance(fetched[0], tuple):
                summary["errors"].append(f"could not fetch message {num.decode()}")
                continue
            item = parse_message(fetched[0][1])
            if item is None:
                summary["skipped"] += 1
                conn.store(num, "+FLAGS", "\\Seen")
                continue
            mid = item["message_id"]
            if mid and vk.sismember(SEEN_KEY, mid):
                summary["skipped"] += 1
                conn.store(num, "+FLAGS", "\\Seen")
                continue
            try:
                result = process_fn(item)
            except Exception as e:  # leave unread so the next poll retries it
                summary["errors"].append(f"{type(e).__name__}: {e}")
                continue
            if mid:
                vk.sadd(SEEN_KEY, mid)
            conn.store(num, "+FLAGS", "\\Seen")
            summary["processed"] += 1
            summary["tickets"].append(result.get("ticket_id"))
    finally:
        try:
            conn.logout()
        except Exception:
            pass
    return summary


# ── auto-reply ──────────────────────────────────────────────

def send_reply(item: dict, result: dict) -> bool:
    """Email the customer the auto-resolution. No-op unless EMAIL_AUTO_REPLY=true."""
    if not auto_reply_enabled() or not item.get("sender"):
        return False
    user = os.getenv("SMTP_USER") or os.getenv("IMAP_USER")
    password = os.getenv("SMTP_PASSWORD") or os.getenv("IMAP_PASSWORD")
    if not (user and password):
        return False

    res = result.get("resolution", {})
    answer = res.get("resolution") or ""
    source = res.get("source_article") or ""
    body = (
        "Hi,\n\n"
        "Thanks for getting in touch. Based on our knowledge base, this should help:\n\n"
        f"{answer}\n\n"
        + (f"Reference: {source}\n\n" if source else "")
        + "If this doesn't solve it, just reply to this email and a person will take over.\n\n"
        f"Ticket: {result.get('ticket_id')}\n"
    )
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_FROM") or user
    msg["To"] = item["sender"]
    msg["Subject"] = "Re: " + (item.get("subject") or "your request")
    msg["Auto-Submitted"] = "auto-replied"
    msg["Precedence"] = "auto_reply"
    if item.get("message_id"):
        msg["In-Reply-To"] = item["message_id"]
        msg["References"] = item["message_id"]
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(os.getenv("SMTP_HOST", "smtp.gmail.com"),
                              int(os.getenv("SMTP_PORT", 465))) as s:
            s.login(user, password)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"[email] auto-reply failed: {type(e).__name__}")
        return False
