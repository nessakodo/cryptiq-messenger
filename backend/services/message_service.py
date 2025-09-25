"""Message serialization helpers shared between REST and websocket flows."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from ..crypto import dilithium_utils, kyber_utils, protocol, symmetric


def decrypt_delivery_for_session(delivery: Dict[str, Any], session_info: Dict[str, str]) -> bytes:
    """Decrypt an encrypted message delivery for a logged-in session."""

    shared_secret = kyber_utils.decapsulate(session_info["kyber_private_key"], delivery["kem_ciphertext"])
    plaintext = symmetric.decrypt(
        shared_secret,
        delivery["nonce"],
        delivery["tag"],
        delivery["ciphertext"],
    )
    return plaintext


def verify_signature(message: Dict[str, Any], plaintext: bytes, sender: Dict[str, Any]) -> bool:
    """Verify the Dilithium signature for the provided plaintext."""

    created_at = message.get("created_at") or message.get("message_created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    timestamp_iso = protocol.canonical_timestamp(created_at)
    payload = protocol.build_signature_payload(sender["username"], plaintext, timestamp_iso)
    return dilithium_utils.verify(sender["dilithium_public_key"], payload, message["signature"])


def serialize_delivery(
    message: Dict[str, Any],
    delivery: Dict[str, Any],
    sender: Dict[str, Any],
    plaintext: bytes,
    signature_valid: bool,
) -> Dict[str, object]:
    """Return a JSON-serialisable payload for clients."""

    created_at = message.get("created_at") or message.get("message_created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    timestamp_iso = protocol.canonical_timestamp(created_at)
    return {
        "id": message["id"] if "id" in message else message.get("message_id"),
        "sender": sender["username"],
        "plaintext": plaintext.decode("utf-8"),
        "ciphertext": delivery["ciphertext"],
        "nonce": delivery["nonce"],
        "tag": delivery["tag"],
        "kem_ciphertext": delivery["kem_ciphertext"],
        "signature": message["signature"],
        "signature_valid": signature_valid,
        "timestamp": timestamp_iso,
    }
