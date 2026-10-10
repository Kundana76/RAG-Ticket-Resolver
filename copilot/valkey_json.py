# -*- coding: utf-8 -*-
"""
Valkey JSON helpers.

valkey-bundle includes the JSON module, so we can use:
  JSON.SET  key  $  '{...}'
  JSON.GET  key  $
  JSON.NUMINCRBY key $.field 1

redis-py exposes these via client.json() when the module is loaded.
Falls back to plain SET/GET (string JSON) when using fakeredis,
which doesn't support the JSON module.
"""
import json
from valkey_config import get_client


def json_set(key: str, value: dict, ttl: int | None = None) -> None:
    """Store a dict as a JSON document at key."""
    client = get_client()
    try:
        # Try native JSON module (valkey-bundle)
        client.json().set(key, "$", value)
        if ttl:
            client.expire(key, ttl)
    except Exception:
        # Fallback: plain string JSON (fakeredis / no JSON module)
        if ttl:
            client.set(key, json.dumps(value), ex=ttl)
        else:
            client.set(key, json.dumps(value))


def json_get(key: str) -> dict | None:
    """Retrieve a JSON document from key. Returns None if not found."""
    client = get_client()
    try:
        result = client.json().get(key, "$")
        if result:
            return result[0] if isinstance(result, list) else result
        return None
    except Exception:
        raw = client.get(key)
        if raw:
            return json.loads(raw)
        return None


def json_numincrby(key: str, path: str, amount: float) -> float | None:
    """Atomically increment a numeric field in a JSON document."""
    client = get_client()
    try:
        result = client.json().numincrby(key, path, amount)
        return result[0] if isinstance(result, list) else result
    except Exception:
        # Fallback: read-modify-write (not atomic, but fine for demo)
        raw = client.get(key)
        if not raw:
            return None
        doc = json.loads(raw)
        # Simple single-level path like "$.field" -> "field"
        field = path.lstrip("$.")
        doc[field] = doc.get(field, 0) + amount
        client.set(key, json.dumps(doc))
        return doc[field]
