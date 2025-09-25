"""Symmetric encryption helpers layered on top of Kyber shared secrets."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from hashlib import sha256

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


NONCE_BYTES = 12


@dataclass
class CipherBundle:
    nonce: str
    ciphertext: str
    tag: str


def _derive_key(shared_secret_b64: str) -> bytes:
    secret_bytes = base64.b64decode(shared_secret_b64)
    return sha256(secret_bytes).digest()


def encrypt(shared_secret_b64: str, plaintext: bytes) -> CipherBundle:
    """Encrypt plaintext bytes using AES-256-GCM derived from the shared secret."""

    key = _derive_key(shared_secret_b64)
    nonce = get_random_bytes(NONCE_BYTES)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return CipherBundle(
        nonce=base64.b64encode(nonce).decode(),
        ciphertext=base64.b64encode(ciphertext).decode(),
        tag=base64.b64encode(tag).decode(),
    )


def decrypt(shared_secret_b64: str, nonce_b64: str, tag_b64: str, ciphertext_b64: str) -> bytes:
    """Decrypt ciphertext bytes using AES-256-GCM derived from the shared secret."""

    key = _derive_key(shared_secret_b64)
    nonce = base64.b64decode(nonce_b64)
    tag = base64.b64decode(tag_b64)
    ciphertext = base64.b64decode(ciphertext_b64)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)
