# 𝘊𝘙𝘠𝘗𝘛𝘐𝘘 — Post-Quantum Secure Messenger

[![Version](https://img.shields.io/badge/Version-v1.0.0-000000?style=for-the-badge&logo=github&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-000000?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![MIT License](https://img.shields.io/badge/License-MIT-000000?style=for-the-badge)](LICENSE)

CRYPTIQ is a full-stack reference implementation that demonstrates **practical post-quantum encrypted messaging**. The stack combines a Next.js front end with a Flask-SocketIO back end powered by NIST-selected primitives — Kyber-768 for key encapsulation and Dilithium-3 for digital signatures — via the [Open Quantum Safe](https://openquantumsafe.org) `oqs` bindings.

---

## ✨ What’s new in this release

- **Real Kyber-768 + Dilithium-3 integration** using `oqs` with per-recipient encapsulation and Dilithium signatures over canonical payloads.
- **Password-protected key vault**: user private keys are wrapped with scrypt + AES-GCM and persisted in SQLite through lightweight helpers.
- **Authenticated sessions** with token-based login/logout, in-memory decrypted key cache, and Socket.IO join authorization.
- **Encrypted message pipeline**: each outgoing message is signed, encapsulated for every recipient, sealed with AES-256-GCM, and verified on delivery.
- **Cryptography-aware UI**: the chat surface shows signature verification state, ciphertext metadata, and exposes a decrypt helper endpoint for experimentation.

---

## 🔐 Architecture overview

| Layer | Technology | Responsibilities |
|-------|------------|------------------|
| Frontend | Next.js + TailwindCSS | Auth modal, Socket.IO client, renders PQ telemetry and chat experience. |
| Transport | Socket.IO | Authenticated, per-session channels for message fan-out. |
| Backend | Flask, Flask-SocketIO | REST APIs for auth, message orchestration, PQ crypto operations. |
| Crypto | `oqs`, PyCryptodome | Kyber-768 KEM, Dilithium-3 signatures, AES-256-GCM symmetric layer, scrypt password KDF. |
| Persistence | SQLite | Users, sessions, messages, and per-recipient ciphertext packages. |

### Message lifecycle
1. **Registration/Login** – users supply a username + password. The backend mints Kyber/Dilithium keypairs, encrypts private keys with scrypt+AES, and returns public/private material to the client.
2. **Session establishment** – successful auth stores decrypted keys in a locked session cache and issues a bearer token. Socket joins are validated against this token.
3. **Send flow** – plaintext is canonicalised, Dilithium-signed, and encrypted for every recipient via Kyber encapsulation → AES-GCM. Each bundle is stored alongside the message record.
4. **Receive flow** – recipients obtain encrypted payloads over Socket.IO. The server also verifies Dilithium signatures and, for convenience, attaches the decrypted plaintext plus raw cryptographic artefacts.
5. **History sync** – reconnecting users replay their encrypted deliveries from SQLite, preserving signature verification state and ciphertext metadata.

---

## 🚀 Quick start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m backend.app
```

The API listens on `http://localhost:5002` and stores state in `backend/instance/cryptiq.db`.

> ℹ️ Install `pip install oqs` to enable true Kyber/Dilithium primitives. Without it the server falls back to a deterministic shim for development purposes.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Next.js serves the UI on `http://localhost:3000`. Set `NEXT_PUBLIC_BACKEND_URL` in `.env.local` if your backend runs elsewhere.

---

## 📡 API highlights

- `POST /api/auth/register` – create an account, receive PQ key pairs (base64) and session token.
- `POST /api/auth/login` – unlock stored keys and obtain a fresh token.
- `POST /api/auth/logout` – invalidate the active token.
- `GET /api/messages` – fetch encrypted deliveries for the authenticated user, including decrypted plaintext and Dilithium verification status.
- `POST /api/messages` – submit plaintext; server signs, encrypts, stores, and broadcasts per-recipient packages.
- `POST /api/messages/decrypt` – utility endpoint that decapsulates and decrypts a ciphertext bundle using the caller’s session keys.

All protected routes expect a `Bearer <token>` header issued during login/registration.

---

## 🛡️ Security notes

- **Post-quantum primitives** – Kyber-768 KEM and Dilithium-3 signatures via the Open Quantum Safe project.
- **Symmetric confidentiality** – AES-256-GCM keys are derived from Kyber shared secrets using SHA-256.
- **Key protection** – user private keys are encrypted at rest with scrypt-derived AES keys keyed by the user’s password.
- **Session hygiene** – decrypted key material lives only in an in-memory cache bound to bearer tokens; tokens can be revoked with the logout endpoint.
- **Telemetry** – every UI message shows signature verification state and exposes raw ciphertext/nonce/tag values to aid demonstrations and audits.

> **Limitations:** the server currently performs encryption on behalf of clients so messages remain visible to the service for demo purposes. Bringing the same PQ operations to the browser (e.g., via WebAssembly) is the next step for full end-to-end secrecy.

---

## 🧪 Development tips

- Run `pytest` inside `backend` to execute the crypto regression tests.
- Delete `backend/instance/cryptiq.db` to reset users and message history.
- Socket.IO broadcasts target only authenticated sessions; open multiple browser tabs and log in with different accounts to observe per-user ciphertext fan-out.

---

## 📜 License & credits

Created by [Nessa Kodo](https://nessakodo.com). Licensed under the MIT License.

“Quantum-safe chat. For every future.”
