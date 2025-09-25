"""AES-256 GCM authenticated encryption."""

from __future__ import annotations

import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def encrypt(key: bytes, plaintext: bytes) -> str:
    """Encrypt a plaintext with AES-256 GCM and return a base64-encoded string."""

    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return b".".join(
        map(
            base64.b64encode,
            [
                cipher.nonce,
                tag,
                ciphertext,
            ],
        )
    ).decode("utf-8")


def decrypt(key: bytes, encrypted_b64: str) -> bytes:
    """Decrypt a base64-encoded AES-256 GCM ciphertext."""

    nonce, tag, ciphertext = map(base64.b64decode, encrypted_b64.split(b"."))
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)