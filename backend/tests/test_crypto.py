import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

os.environ["DATABASE_URL"] = f"sqlite:///{Path(__file__).parent / 'test.db'}"

import json

import pytest

from backend.app import create_app
from backend.crypto import dilithium_utils, kyber_utils, symmetric


@pytest.fixture(scope="module")
def app():
    test_app = create_app()
    yield test_app
    db_path = Path(os.environ["DATABASE_URL"].replace("sqlite:///", ""))
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def client(app):
    return app.test_client()


def test_kyber_roundtrip():
    public_key, secret_key = kyber_utils.generate_keypair()
    ciphertext, shared_secret_enc = kyber_utils.encapsulate(public_key)
    shared_secret_dec = kyber_utils.decapsulate(secret_key, ciphertext)
    assert shared_secret_enc == shared_secret_dec


def test_dilithium_sign_verify():
    public_key, secret_key = dilithium_utils.generate_keypair()
    message = b"quantum-secure"
    signature = dilithium_utils.sign(secret_key, message)
    assert dilithium_utils.verify(public_key, message, signature)
    assert not dilithium_utils.verify(public_key, b"tampered", signature)


def test_symmetric_encrypt_decrypt():
    pub, priv = kyber_utils.generate_keypair()
    ciphertext, shared_enc = kyber_utils.encapsulate(pub)
    shared_dec = kyber_utils.decapsulate(priv, ciphertext)
    bundle = symmetric.encrypt(shared_enc, b"hello")
    plaintext = symmetric.decrypt(shared_dec, bundle.nonce, bundle.tag, bundle.ciphertext)
    assert plaintext == b"hello"


def test_message_flow(client):
    alice = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "wonderland"},
    ).get_json()
    bob = client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "builder"},
    ).get_json()

    send_response = client.post(
        "/api/messages",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"message": "Hello Bob"},
    )
    assert send_response.status_code == 200
    payload = send_response.get_json()["message"]
    assert payload["signature_valid"] is True
    assert payload["plaintext"] == "Hello Bob"

    history = client.get(
        "/api/messages",
        headers={"Authorization": f"Bearer {bob['token']}"},
    ).get_json()
    assert any(msg["plaintext"] == "Hello Bob" for msg in history["messages"])

    bob_view = next(msg for msg in history["messages"] if msg["plaintext"] == "Hello Bob")
    decrypt_body = {
        key: bob_view[key]
        for key in ("kem_ciphertext", "nonce", "tag", "ciphertext")
    }
    decrypt_response = client.post(
        "/api/messages/decrypt",
        headers={"Authorization": f"Bearer {bob['token']}"},
        data=json.dumps(decrypt_body),
        content_type="application/json",
    )
    assert decrypt_response.status_code == 200
    assert decrypt_response.get_json()["plaintext"] == "Hello Bob"
