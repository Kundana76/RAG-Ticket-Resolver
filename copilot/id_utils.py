# -*- coding: utf-8 -*-
"""
ID Utilities — UUIDv7 with domain prefix.

Follows the hackathon ID strategy:
  {domain}:{uuidv7}

UUIDv7 embeds a Unix timestamp in the most-significant bits, giving:
  - Monotonic ordering (sortable by creation time)
  - K-sortable in Valkey Sorted Sets
  - No coordination needed (client-side generation)

Since Python's `uuid` stdlib doesn't have v7 yet, we implement it manually.
"""
import os
import time
import struct
import random


def _uuidv7() -> str:
    """Generate a UUIDv7 string (RFC 9562)."""
    # 48-bit Unix timestamp in milliseconds
    ts_ms = int(time.time() * 1000) & 0xFFFFFFFFFFFF
    # 12 random bits (seq)
    rand_a = random.getrandbits(12)
    # 62 random bits
    rand_b = random.getrandbits(62)

    # Pack: 48-bit ts | 4-bit ver(7) | 12-bit rand_a | 2-bit var(10) | 62-bit rand_b
    hi = (ts_ms << 16) | (0x7 << 12) | rand_a
    lo = (0b10 << 62) | rand_b

    # Format as UUID string
    b = struct.pack(">QQ", hi, lo)
    hex_str = b.hex()
    return (
        f"{hex_str[0:8]}-{hex_str[8:12]}-"
        f"{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"
    )


def create_id(domain: str) -> str:
    """Create a domain-prefixed UUIDv7 ID.

    Examples:
        create_id("ticket")  -> "ticket:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e"
        create_id("session") -> "session:0192d4f0-1a2b-7c3d-8e4f-5a6b7c8d9e0f"
    """
    return f"{domain}:{_uuidv7()}"


def parse_id(full_id: str) -> tuple[str, str]:
    """Parse a domain-prefixed ID into (domain, uuid)."""
    colon = full_id.index(":")
    return full_id[:colon], full_id[colon + 1:]
