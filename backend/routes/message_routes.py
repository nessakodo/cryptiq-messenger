"""Message-related endpoints for sending and retrieving."""

from __future__ import annotations

import hashlib
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request

from .. import storage
from ..crypto import dilithium_utils, kyber_utils, protocol, symmetric
from ..session import Session
from ..websocket.socket_server import socketio


message_routes = Blueprint("messages", __name__)


def _get_json() -> Dict[str, Any]:
    return request.get_json(force=True, silent=True) or {}


def _auth_session() -> Session:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise ValueError("missing bearer token")
    token = header[7:]
    cache = current_app.config["SESSION_CACHE"]
    session = cache.get(token)
    if not session:
        raise ValueError("invalid or expired session")
    return session


@message_routes.route("/api/messages/send", methods=["POST"])
def send() -> Any:
    session = _auth_session()
    data = _get_json()
    recipient_username = data.get("recipient_username")
    plaintext = (data.get("plaintext") or "").encode("utf-8")

    if not recipient_username or not plaintext:
        return jsonify({"error": "recipient_username and plaintext are required"}), 400

    recipient = storage.get_user_by_username(recipient_username)
    if not recipient:
        return jsonify({"error": f"user not found: {recipient_username}"}), 404

    now = current_app.config["NOW_FN"]()
    timestamp_iso = protocol.canonical_timestamp(now)

    signature_payload = protocol.build_signature_payload(
        sender_username=session.username,
        plaintext=plaintext,
        timestamp_iso=timestamp_iso,
    )
    signature = dilithium_utils.sign(
        session.dilithium_private_key,
        signature_payload,
    )

    message_id = storage.create_message(
        sender_id=session.user_id,
        signature=signature,
        plaintext_digest=hashlib.sha256(plaintext).hexdigest(),
        created_at=timestamp_iso,
    )

    kem_ciphertext, shared_secret = kyber_utils.encapsulate(recipient["kyber_public_key"])
    encrypted_payload = symmetric.encrypt(shared_secret, plaintext)
    nonce, tag, ciphertext = encrypted_payload.split(".")

    storage.create_delivery(
        message_id=message_id,
        recipient_id=recipient["id"],
        kem_ciphertext=kem_ciphertext,
        nonce=nonce,
        tag=tag,
        ciphertext=ciphertext,
        created_at=timestamp_iso,
    )

    socket_registry = current_app.config["SOCKET_REGISTRY"]
    recipient_socket = socket_registry.get(recipient["id"])
    if recipient_socket:
        recipient_socket.emit("new_message", {"message_id": message_id})

    return ("", 204)


@message_routes.route("/api/messages", methods=["GET"])
def get_all() -> Any:
    session = _auth_session()
    deliveries = storage.deliveries_for_user(session.user_id)

    messages = []
    for delivery in deliveries:
        shared_secret = kyber_utils.decapsulate(
            session.kyber_private_key,
            delivery["kem_ciphertext"],
        )
        encrypted_payload = f"{delivery['nonce']}.{delivery['tag']}.{delivery['ciphertext']}"
        plaintext = symmetric.decrypt(shared_secret, encrypted_payload)

        signature_payload = protocol.build_signature_payload(
            sender_username=delivery["sender_username"],
            plaintext=plaintext,
            timestamp_iso=protocol.canonical_timestamp(delivery["message_created_at"]),
        )
        if not dilithium_utils.verify(
            delivery["dilithium_public_key"],
            signature_payload,
            delivery["signature"],
        ):
            continue  # Skip messages with invalid signatures

        messages.append(
            {
                "id": delivery["message_id"],
                "sender_username": delivery["sender_username"],
                "plaintext": plaintext.decode("utf-8"),
                "created_at": protocol.canonical_timestamp(delivery["message_created_at"]),
            }
        )

    return jsonify(messages)