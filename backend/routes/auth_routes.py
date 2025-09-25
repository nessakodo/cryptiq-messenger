"""Authentication endpoints handling registration, login, and logout."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..crypto import dilithium_utils, keywrap, kyber_utils, protocol
from .. import storage


auth_routes = Blueprint("auth", __name__)


def _get_json() -> Dict[str, Any]:
    return request.get_json(force=True, silent=True) or {}


def _extract_token() -> Optional[str]:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    data = _get_json()
    token = data.get("token") if isinstance(data, dict) else None
    return token


SESSION_DURATION_HOURS = 12


def _cache_session(token: str, user: Dict[str, Any], kyber_priv: str, dilithium_priv: str) -> None:
    cache = current_app.config["SESSION_CACHE"]
    cache.store(
        token,
        {
            "user_id": user["id"],
            "username": user["username"],
            "kyber_private_key": kyber_priv,
            "dilithium_private_key": dilithium_priv,
            "kyber_public_key": user["kyber_public_key"],
            "dilithium_public_key": user["dilithium_public_key"],
        },
    )


def _session_payload(user: Dict[str, Any], token: str, kyber_priv: str, dilithium_priv: str) -> Dict[str, Any]:
    created_at = user.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "created_at": protocol.canonical_timestamp(created_at),
        },
        "keys": {
            "kyber": {"public": user["kyber_public_key"], "private": kyber_priv},
            "dilithium": {
                "public": user["dilithium_public_key"],
                "private": dilithium_priv,
            },
        },
    }


@auth_routes.route("/api/auth/register", methods=["POST"])
def register() -> Any:
    data = _get_json()
    username = (data.get("username") or "").strip()
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    if storage.get_user_by_username(username):
        return jsonify({"error": "username already exists"}), 409

    kyber_pub, kyber_priv = kyber_utils.generate_keypair()
    dilithium_pub, dilithium_priv = dilithium_utils.generate_keypair()

    created_at = datetime.utcnow().isoformat()
    user = storage.create_user(
        username=username,
        password_hash=generate_password_hash(password),
        kyber_public_key=kyber_pub,
        kyber_private_key_enc=keywrap.encrypt_secret(password, kyber_priv),
        dilithium_public_key=dilithium_pub,
        dilithium_private_key_enc=keywrap.encrypt_secret(password, dilithium_priv),
        created_at=created_at,
    )
    token = secrets.token_urlsafe(48)
    now_iso = datetime.utcnow().isoformat()
    expires_iso = (datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS)).isoformat()
    storage.create_session(user["id"], token, now_iso, expires_iso)

    _cache_session(token, user, kyber_priv, dilithium_priv)
    return jsonify(_session_payload(user, token, kyber_priv, dilithium_priv)), 201


@auth_routes.route("/api/auth/login", methods=["POST"])
def login() -> Any:
    data = _get_json()
    username = (data.get("username") or "").strip()
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    user = storage.get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "invalid credentials"}), 401

    kyber_priv = keywrap.decrypt_secret(password, user["kyber_private_key_enc"])
    dilithium_priv = keywrap.decrypt_secret(password, user["dilithium_private_key_enc"])

    token = secrets.token_urlsafe(48)
    now_iso = datetime.utcnow().isoformat()
    expires_iso = (datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS)).isoformat()
    storage.create_session(user["id"], token, now_iso, expires_iso)

    _cache_session(token, user, kyber_priv, dilithium_priv)
    return jsonify(_session_payload(user, token, kyber_priv, dilithium_priv))


@auth_routes.route("/api/auth/logout", methods=["POST"])
def logout() -> Any:
    token = _extract_token()
    if not token:
        return jsonify({"error": "missing bearer token"}), 400

    storage.delete_session(token)
    current_app.config["SESSION_CACHE"].remove(token)
    return ("", 204)
