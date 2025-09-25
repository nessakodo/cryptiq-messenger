"""Socket.IO server that streams encrypted messages to authenticated clients."""

from __future__ import annotations

from flask import current_app, request
from flask_socketio import SocketIO, emit

from .. import storage
from ..services.message_service import decrypt_delivery_for_session, serialize_delivery, verify_signature


socketio = SocketIO(cors_allowed_origins="*")


@socketio.on("join")
def handle_join(data):  # type: ignore[override]
    token = (data or {}).get("token")
    if not token:
        emit("error", {"error": "authentication token required"})
        return

    session_cache = current_app.config["SESSION_CACHE"]
    session_info = session_cache.get(token)
    if not session_info:
        emit("error", {"error": "invalid session"})
        return

    registry = current_app.config["SOCKET_REGISTRY"]
    registry.register(token, session_info["user_id"], request.sid)

    emit("status", {"message": "connected", "username": session_info["username"]})

    deliveries = storage.deliveries_for_user(session_info["user_id"])

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
        emit(
            "receive_message",
            serialize_delivery(message, delivery, sender, plaintext, signature_valid),
        )


@socketio.on("disconnect")
def handle_disconnect():  # type: ignore[override]
    registry = current_app.config["SOCKET_REGISTRY"]
    registry.unregister_sid(request.sid)
