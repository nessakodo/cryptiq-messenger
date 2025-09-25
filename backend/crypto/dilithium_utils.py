"""Dilithium-3 signature helpers with optional Open Quantum Safe support."""

from __future__ import annotations

import base64
import hmac
import warnings
from contextlib import contextmanager
from typing import Iterator, Tuple

from Crypto.Hash import SHA512
from Crypto.Random import get_random_bytes

try:  # pragma: no cover
    import oqs

    HAVE_OQS = True
except Exception:  # pragma: no cover - deterministic shim
    oqs = None
    HAVE_OQS = False
    warnings.warn(
        "liboqs bindings not available. Falling back to deterministic Dilithium shim "
        "(not quantum-safe). Install the 'oqs' package for real Dilithium-3 support.",
        RuntimeWarning,
    )


@contextmanager
def _sig() -> Iterator["oqs.Signature"]:
    signer = oqs.Signature("Dilithium3")
    try:
        yield signer
    finally:
        signer.free()


def _oqs_generate() -> Tuple[str, str]:
    with _sig() as signer:
        public_key, secret_key = signer.generate_keypair()
    return base64.b64encode(public_key).decode(), base64.b64encode(secret_key).decode()


def _oqs_sign(private_key_b64: str, message: bytes) -> str:
    private_key = base64.b64decode(private_key_b64)
    with _sig() as signer:
        signature = signer.sign(message, private_key)
    return base64.b64encode(signature).decode()


def _oqs_verify(public_key_b64: str, message: bytes, signature_b64: str) -> bool:
    public_key = base64.b64decode(public_key_b64)
    signature = base64.b64decode(signature_b64)
    with _sig() as signer:
        return signer.verify(message, signature, public_key)


def _shim_generate() -> Tuple[str, str]:
    secret = get_random_bytes(32)
    return base64.b64encode(secret).decode(), base64.b64encode(secret).decode()


def _shim_sign(private_key_b64: str, message: bytes) -> str:
    secret = base64.b64decode(private_key_b64)
    signature = hmac.new(secret, message, SHA512).digest()
    return base64.b64encode(signature).decode()


def _shim_verify(public_key_b64: str, message: bytes, signature_b64: str) -> bool:
    key = base64.b64decode(public_key_b64)
    expected = hmac.new(key, message, SHA512).digest()
    signature = base64.b64decode(signature_b64)
    return hmac.compare_digest(expected, signature)


def generate_keypair() -> Tuple[str, str]:
    return _oqs_generate() if HAVE_OQS else _shim_generate()


def sign(private_key_b64: str, message: bytes) -> str:
    return _oqs_sign(private_key_b64, message) if HAVE_OQS else _shim_sign(private_key_b64, message)


def verify(public_key_b64: str, message: bytes, signature_b64: str) -> bool:
    return _oqs_verify(public_key_b64, message, signature_b64) if HAVE_OQS else _shim_verify(public_key_b64, message, signature_b64)
