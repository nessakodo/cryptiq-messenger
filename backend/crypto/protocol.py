"""Shared helpers for constructing signed payloads and timestamps."""

from __future__ import annotations

from datetime import datetime, timezone


def canonical_timestamp(timestamp: datetime) -> str:
    """Return an ISO-8601 UTC timestamp string with a trailing Z."""

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    else:
        timestamp = timestamp.astimezone(timezone.utc)
    return timestamp.isoformat().replace("+00:00", "Z")


def build_signature_payload(sender_username: str, plaintext: bytes, timestamp_iso: str) -> bytes:
    """Create a canonical byte payload for Dilithium signatures."""

    return b"|".join(
        [
            sender_username.encode("utf-8"),
            timestamp_iso.encode("utf-8"),
            plaintext,
        ]
    )
