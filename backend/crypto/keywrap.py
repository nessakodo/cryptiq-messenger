"""Helpers for encrypting sensitive key material with user passwords."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Dict

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes


SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
KEY_BYTES = 32
NONCE_BYTES = 12
SALT_BYTES = 16


@dataclass
class EncryptedBlob:
    """Encrypted payload metadata stored in the database."""

    salt: str
    nonce: str
    tag: str
    ciphertext: str

    def to_json(self) -> str:
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(data: str) -> "EncryptedBlob":
        payload: Dict[str, str] = json.loads(data)
        return EncryptedBlob(**payload)


def _derive_key(password: str, salt: bytes) -> bytes:
    return scrypt(password.encode("utf-8"), salt, KEY_BYTES, N=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)


def encrypt_secret(password: str, secret_b64: str) -> str:
    """Encrypt a base64 encoded secret with a password and return JSON metadata."""

    salt = get_random_bytes(SALT_BYTES)
    key = _derive_key(password, salt)
    nonce = get_random_bytes(NONCE_BYTES)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(base64.b64decode(secret_b64))
    blob = EncryptedBlob(
        salt=base64.b64encode(salt).decode(),
        nonce=base64.b64encode(nonce).decode(),
        tag=base64.b64encode(tag).decode(),
        ciphertext=base64.b64encode(ciphertext).decode(),
    )
    return blob.to_json()


def decrypt_secret(password: str, payload_json: str) -> str:
    """Decrypt a password-protected secret and return it encoded as base64."""

    blob = EncryptedBlob.from_json(payload_json)
    salt = base64.b64decode(blob.salt)
    nonce = base64.b64decode(blob.nonce)
    tag = base64.b64decode(blob.tag)
    ciphertext = base64.b64decode(blob.ciphertext)
    key = _derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    secret = cipher.decrypt_and_verify(ciphertext, tag)
    return base64.b64encode(secret).decode()
