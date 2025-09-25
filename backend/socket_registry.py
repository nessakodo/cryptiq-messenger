"""Track active Socket.IO connections by authentication token."""

from __future__ import annotations

from collections import defaultdict
from threading import RLock
from typing import Dict, Iterable


class SocketRegistry:
    """Thread-safe registry mapping tokens to Socket.IO session IDs."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._token_to_sid: Dict[str, str] = {}
        self._sid_to_token: Dict[str, str] = {}
        self._user_to_tokens: Dict[int, set[str]] = defaultdict(set)

    def register(self, token: str, user_id: int, sid: str) -> None:
        with self._lock:
            self._token_to_sid[token] = sid
            self._sid_to_token[sid] = token
            self._user_to_tokens[user_id].add(token)

    def unregister(self, token: str) -> None:
        with self._lock:
            sid = self._token_to_sid.pop(token, None)
            if not sid:
                return
            self._sid_to_token.pop(sid, None)
            for user_id, tokens in list(self._user_to_tokens.items()):
                if token in tokens:
                    tokens.remove(token)
                if not tokens:
                    self._user_to_tokens.pop(user_id, None)

    def sid_for_token(self, token: str) -> str | None:
        with self._lock:
            return self._token_to_sid.get(token)

    def token_for_sid(self, sid: str) -> str | None:
        with self._lock:
            return self._sid_to_token.get(sid)

    def sids_for_user(self, user_id: int) -> Iterable[str]:
        with self._lock:
            tokens = self._user_to_tokens.get(user_id, set())
            return [self._token_to_sid[token] for token in tokens if token in self._token_to_sid]

    def unregister_sid(self, sid: str) -> None:
        with self._lock:
            token = self._sid_to_token.pop(sid, None)
            if not token:
                return
            self._token_to_sid.pop(token, None)
            for user_id, tokens in list(self._user_to_tokens.items()):
                if token in tokens:
                    tokens.remove(token)
                if not tokens:
                    self._user_to_tokens.pop(user_id, None)
