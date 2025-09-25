"""Routes for creating and retrieving post-quantum encrypted messages."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, current_app, jsonify, request

from ..crypto import dilithium_utils, kyber_utils, protocol, symmetric
from .. import storage
from ..services.message_service import decrypt_delivery_for_session, serialize_delivery, verify_signature
from ..websocket.socket_server import socketio


message_routes = Blueprint("messages", __name__)


def _get_json() -> Dict[str, Any]:
    return request.get_json(force=True, silent=True) or {}


def _extract_token() -> Optional[str]:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    payload = _get_json()
    token = payload.get("token") if isinstance(payload, dict) else None
    return token


def _require_session() -> Tuple[Optional[str], Optional[Dict[str, str]], Optional[Any]]:
    token = _extract_token()
    if not token:
        return None, None, jsonify({"error": "missing bearer token"}), 401
    cache = current_app.config["SESSION_CACHE"]
    session_info = cache.get(token)
    if not session_info:
        return None, None, jsonify({"error": "invalid or expired session"}), 401
    return token, session_info, None, None


@message_routes.route("/api/messages", methods=["POST"])
def send_message() -> Any:
    token, session_info, error_response, status = _require_session()
    if error_response is not None:
        return error_response, status

    data = _get_json()
    plaintext = (data.get("message") or "").strip()
    if not plaintext:
        return jsonify({"error": "message body is required"}), 400

    plaintext_bytes = plaintext.encode("utf-8")
    now = current_app.config["NOW_FN"]()
    timestamp_iso = protocol.canonical_timestamp(now)
    payload_to_sign = protocol.build_signature_payload(
        session_info["username"], plaintext_bytes, timestamp_iso
    )
    signature = dilithium_utils.sign(session_info["dilithium_private_key"], payload_to_sign)

    sender = storage.get_user_by_id(session_info["user_id"])
    if not sender:
        return jsonify({"error": "sender not found"}), 400

    digest = hashlib.sha256(plaintext_bytes).hexdigest()
    message_id = storage.create_message(
        sender_id=sender["id"],
        signature=signature,
        plaintext_digest=digest,
        created_at=now.isoformat(),
    )

    message_record = {
        "id": message_id,
        "sender_id": sender["id"],
        "signature": signature,
        "plaintext_digest": digest,
        "created_at": now.isoformat(),
    }

    signature_valid = dilithium_utils.verify(
        sender["dilithium_public_key"], payload_to_sign, signature
    )
    if not signature_valid:  # pragma: no cover - defensive guard
        raise ValueError("self-signature verification failed")

    payloads = []
    for recipient in storage.list_users():
        kem_ciphertext, shared_secret = kyber_utils.encapsulate(recipient["kyber_public_key"])
        cipher_bundle = symmetric.encrypt(shared_secret, plaintext_bytes)
        storage.create_delivery(
            message_id=message_id,
            recipient_id=recipient["id"],
            kem_ciphertext=kem_ciphertext,
            nonce=cipher_bundle.nonce,
            tag=cipher_bundle.tag,
            ciphertext=cipher_bundle.ciphertext,
            created_at=now.isoformat(),
        )
        delivery_record = {
            "message_id": message_id,
            "recipient_id": recipient["id"],
            "kem_ciphertext": kem_ciphertext,
            "nonce": cipher_bundle.nonce,
            "tag": cipher_bundle.tag,
            "ciphertext": cipher_bundle.ciphertext,
            "created_at": now.isoformat(),
        }
        payload = serialize_delivery(
            message=message_record,
            delivery=delivery_record,
            sender=sender,
            plaintext=plaintext_bytes,
            signature_valid=signature_valid,
        )
        payloads.append((recipient["id"], payload))

    registry = current_app.config["SOCKET_REGISTRY"]
    for recipient_id, payload in payloads:
        for sid in registry.sids_for_user(recipient_id):
            socketio.emit("receive_message", payload, room=sid)

    sender_payload = next((p for rid, p in payloads if rid == sender["id"]), payloads[0][1])
    return jsonify({"message": sender_payload})


@message_routes.route("/api/messages", methods=["GET"])
def get_messages() -> Any:
    token, session_info, error_response, status = _require_session()
    if error_response is not None:
        return error_response, status

    deliveries = storage.deliveries_for_user(session_info["user_id"])

    messages: list[Dict[str, Any]] = []
    for record in deliveries:
        delivery = {
            "message_id": record["message_id"],
            "kem_ciphertext": record["kem_ciphertext"],
            "nonce": record["nonce"],
            "tag": record["tag"],
            "ciphertext": record["ciphertext"],
            "created_at": record["created_at"],
        }
        message = {
            "id": record["message_id"],
            "signature": record["signature"],
            "plaintext_digest": record["plaintext_digest"],
            "created_at": record["message_created_at"],
        }
        sender = {
            "id": record["sender_id"],
            "username": record["sender_username"],
            "dilithium_public_key": record["dilithium_public_key"],
        }
        plaintext = decrypt_delivery_for_session(delivery, session_info)
        signature_valid = verify_signature(message, plaintext, sender)
        messages.append(
            serialize_delivery(
                message=message,
                delivery=delivery,
                sender=sender,
                plaintext=plaintext,
                signature_valid=signature_valid,
            )
        )

    return jsonify({"messages": messages})


@message_routes.route("/api/messages/decrypt", methods=["POST"])
def decrypt_message() -> Any:
    token, session_info, error_response, status = _require_session()
    if error_response is not None:
        return error_response, status

    data = _get_json()
    required_fields = {"kem_ciphertext", "nonce", "tag", "ciphertext"}
    if not required_fields.issubset(data.keys()):
        return jsonify({"error": "kem_ciphertext, nonce, tag, and ciphertext are required"}), 400

    shared_secret = kyber_utils.decapsulate(session_info["kyber_private_key"], data["kem_ciphertext"])
    plaintext = symmetric.decrypt(
        shared_secret, data["nonce"], data["tag"], data["ciphertext"]
    )
    return jsonify({"plaintext": plaintext.decode("utf-8")})
