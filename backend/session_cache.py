"""In-memory cache storing decrypted key material for active sessions."""

from __future__ import annotations

from collections import defaultdict
from threading import RLock
from typing import Dict, Iterable, Optional


class SessionCache:
    """Thread-safe mapping of tokens to decrypted key material."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._token_to_session: Dict[str, Dict[str, str]] = {}
        self._user_to_tokens: Dict[int, set[str]] = defaultdict(set)

    def store(self, token: str, session_info: Dict[str, str]) -> None:
        with self._lock:
            self._token_to_session[token] = session_info
            self._user_to_tokens[session_info["user_id"]].add(token)

    def get(self, token: str) -> Optional[Dict[str, str]]:
        with self._lock:
            return self._token_to_session.get(token)

    def remove(self, token: str) -> None:
        with self._lock:
            session_info = self._token_to_session.pop(token, None)
            if session_info:
                tokens = self._user_to_tokens.get(session_info["user_id"])
                if tokens and token in tokens:
                    tokens.remove(token)
                if tokens and not tokens:
                    self._user_to_tokens.pop(session_info["user_id"], None)

    def tokens_for_user(self, user_id: int) -> Iterable[str]:
        with self._lock:
            return list(self._user_to_tokens.get(user_id, set()))
