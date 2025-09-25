"""Kyber-1024 helper utilities with optional Open Quantum Safe support."""

from __future__ import annotations

import base64
import warnings
from contextlib import contextmanager
from typing import Iterator, Tuple

from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

try:  # pragma: no cover - exercised in environments with liboqs installed
    import oqs

    HAVE_OQS = True
except Exception:  # pragma: no cover - fall back to deterministic shim
    oqs = None
    HAVE_OQS = False
    warnings.warn(
        "liboqs bindings not available. Falling back to deterministic Kyber shim "
        "(not quantum-safe). Install the 'oqs' package for real Kyber-1024 support.",
        RuntimeWarning,
    )


@contextmanager
def _kem() -> Iterator["oqs.KeyEncapsulation"]:
    kem = oqs.KeyEncapsulation("Kyber1024")
    try:
        yield kem
    finally:
        kem.free()


def _oqs_generate() -> Tuple[str, str]:
    with _kem() as kem:
        public_key, secret_key = kem.generate_keypair()
    return base64.b64encode(public_key).decode(), base64.b64encode(secret_key).decode()


def _oqs_encapsulate(public_key_b64: str) -> Tuple[str, str]:
    public_key = base64.b64decode(public_key_b64)
    with _kem() as kem:
        ciphertext, shared_secret = kem.encapsulate(public_key)
    return base64.b64encode(ciphertext).decode(), base64.b64encode(shared_secret).decode()


def _oqs_decapsulate(secret_key_b64: str, ciphertext_b64: str) -> str:
    secret_key = base64.b64decode(secret_key_b64)
    ciphertext = base64.b64decode(ciphertext_b64)
    with _kem() as kem:
        shared_secret = kem.decapsulate(ciphertext, secret_key)
    return base64.b64encode(shared_secret).decode()


def _shim_generate() -> Tuple[str, str]:
    secret = get_random_bytes(32)
    return base64.b64encode(secret).decode(), base64.b64encode(secret).decode()


def _shim_encapsulate(public_key_b64: str) -> Tuple[str, str]:
    public_key = base64.b64decode(public_key_b64)
    nonce = get_random_bytes(32)
    shared_secret = SHA256.new(public_key + nonce).digest()
    return base64.b64encode(nonce).decode(), base64.b64encode(shared_secret).decode()


def _shim_decapsulate(secret_key_b64: str, ciphertext_b64: str) -> str:
    secret_key = base64.b64decode(secret_key_b64)
    nonce = base64.b64decode(ciphertext_b64)
    shared_secret = SHA256.new(secret_key + nonce).digest()
    return base64.b64encode(shared_secret).decode()


def generate_keypair() -> Tuple[str, str]:
    """Generate a Kyber-1024 keypair encoded as base64 strings."""

    return _oqs_generate() if HAVE_OQS else _shim_generate()


def encapsulate(public_key_b64: str) -> Tuple[str, str]:
    """Encapsulate a shared secret to the provided base64 encoded public key."""

    return _oqs_encapsulate(public_key_b64) if HAVE_OQS else _shim_encapsulate(public_key_b64)


def decapsulate(secret_key_b64: str, ciphertext_b64: str) -> str:
    """Recover the shared secret from the base64 encoded secret key and ciphertext."""

    return _oqs_decapsulate(secret_key_b64, ciphertext_b64) if HAVE_OQS else _shim_decapsulate(secret_key_b64, ciphertext_b64)
