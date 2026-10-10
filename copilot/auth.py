# -*- coding: utf-8 -*-
"""
Agent authentication.

  * Passwords: scrypt (stdlib) with a per-user random salt.
  * Tokens:    compact HMAC-SHA256 signed tokens  <payload>.<signature>  with expiry.
  * Users:     stored in Valkey hash  user:<name>   (set  users:all  lists names).
  * Roles:     "agent" (work the queue) and "admin" (also reset data, add users).

The very first account created through POST /auth/register becomes the admin;
after that only an admin can add users. You can also bootstrap one from the
environment with ADMIN_USERNAME / ADMIN_PASSWORD.

Env:
  AUTH_SECRET        signing key. If unset a random one is generated at startup,
                     which means everyone is logged out whenever the server restarts.
  AUTH_TOKEN_TTL     token lifetime in seconds (default 28800 = 8h)
  AUTH_REQUIRED      "false" turns protection off (demo mode only)
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time

from fastapi import Header, HTTPException

from valkey_config import get_client

USERS_SET = "users:all"
USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,32}$")
ROLES = ("agent", "admin")
MIN_PASSWORD_LEN = 8

TOKEN_TTL = int(os.getenv("AUTH_TOKEN_TTL", 8 * 3600))

_secret_env = os.getenv("AUTH_SECRET")
if not _secret_env:
    print("[auth] AUTH_SECRET not set — using a random key; logins reset on restart.")
_SECRET = (_secret_env or secrets.token_hex(32)).encode()


def auth_required() -> bool:
    return os.getenv("AUTH_REQUIRED", "true").strip().lower() not in ("0", "false", "no")


def _user_key(name: str) -> str:
    return f"user:{name}"


# ── password hashing ────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_hex, digest_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex),
                                n=2**14, r=8, p=1, dklen=32)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


# a throwaway hash so unknown usernames cost the same time as wrong passwords
_DUMMY_HASH = hash_password("not-a-real-password")


# ── tokens ──────────────────────────────────────────────────

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def issue_token(username: str, role: str, ttl: int | None = None) -> str:
    payload = _b64(json.dumps(
        {"sub": username, "role": role, "exp": int(time.time()) + (ttl or TOKEN_TTL)},
        separators=(",", ":"),
    ).encode())
    sig = _b64(hmac.new(_SECRET, payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{sig}"


def verify_token(token: str) -> dict | None:
    try:
        payload, sig = token.split(".")
        expected = _b64(hmac.new(_SECRET, payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(_unb64(payload))
        if data.get("exp", 0) < time.time():
            return None
        return {"username": data["sub"], "role": data["role"]}
    except Exception:
        return None


# ── user store ──────────────────────────────────────────────

class AuthManager:
    def __init__(self):
        self.vk = get_client()

    def user_count(self) -> int:
        return self.vk.scard(USERS_SET)

    def create_user(self, username: str, password: str, role: str = "agent") -> dict:
        username = username.strip().lower()
        if not USERNAME_RE.match(username):
            raise ValueError("Username must be 3-32 characters: letters, digits, . _ -")
        if len(password) < MIN_PASSWORD_LEN:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LEN} characters")
        if role not in ROLES:
            raise ValueError("Role must be 'agent' or 'admin'")
        if self.vk.sismember(USERS_SET, username):
            raise ValueError("That username is taken")
        self.vk.hset(_user_key(username), mapping={
            "password": hash_password(password),
            "role": role,
            "created_at": str(int(time.time())),
        })
        self.vk.sadd(USERS_SET, username)
        return {"username": username, "role": role}

    def authenticate(self, username: str, password: str) -> dict | None:
        username = (username or "").strip().lower()
        record = self.vk.hgetall(_user_key(username)) if username else {}
        stored = record.get("password") or _DUMMY_HASH
        ok = verify_password(password or "", stored)
        if not record or not ok:
            return None
        return {"username": username, "role": record.get("role", "agent")}

    def list_users(self) -> list[dict]:
        out = []
        for name in sorted(self.vk.smembers(USERS_SET)):
            out.append({"username": name, "role": self.vk.hget(_user_key(name), "role") or "agent"})
        return out

    def bootstrap_from_env(self) -> None:
        name, pw = os.getenv("ADMIN_USERNAME"), os.getenv("ADMIN_PASSWORD")
        if name and pw and not self.vk.sismember(USERS_SET, name.strip().lower()):
            try:
                self.create_user(name, pw, "admin")
                print(f"[auth] Bootstrapped admin '{name.strip().lower()}' from environment.")
            except ValueError as e:
                print(f"[auth] ADMIN_* bootstrap skipped: {e}")


# ── FastAPI dependencies ────────────────────────────────────

def _user_from_header(authorization: str | None) -> dict | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return verify_token(authorization[7:].strip())


def optional_user(authorization: str | None = Header(default=None)) -> dict | None:
    return _user_from_header(authorization)


def require_agent(authorization: str | None = Header(default=None)) -> dict:
    if not auth_required():
        return {"username": "demo", "role": "admin"}
    user = _user_from_header(authorization)
    if not user:
        raise HTTPException(401, "Sign in required", headers={"WWW-Authenticate": "Bearer"})
    return user


def require_admin(authorization: str | None = Header(default=None)) -> dict:
    user = require_agent(authorization)
    if user["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return user
