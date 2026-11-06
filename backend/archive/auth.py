"""Single-account access to the private archive."""

import hashlib
import hmac
import secrets
import time
from collections import deque

from fastapi import HTTPException

COOKIE = "frontier_archive_session"
SESSION_AGE = 12 * 60 * 60
ATTEMPT_WINDOW = 60
ATTEMPT_LIMIT = 12


def password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)


class ArchiveAuth:
    def __init__(self, username: str, verifier: str):
        salt, expected = verifier.split(":", 1)
        self.salt = bytes.fromhex(salt)
        self.expected = bytes.fromhex(expected)
        if not username or len(self.salt) != 16 or len(self.expected) != 64:
            raise ValueError("Configure a valid archive username and password verifier")
        self.username = username.encode()
        self.sessions: dict[str, float] = {}
        self.attempts: deque[float] = deque()

    def admit_attempt(self) -> None:
        now = time.monotonic()
        while self.attempts and self.attempts[0] <= now - ATTEMPT_WINDOW:
            self.attempts.popleft()
        if len(self.attempts) >= ATTEMPT_LIMIT:
            raise HTTPException(
                429, "登录尝试过多，请稍后重试", headers={"Retry-After": str(ATTEMPT_WINDOW)}
            )
        self.attempts.append(now)

    def verify(self, username: str, password: str) -> bool:
        valid_password = hmac.compare_digest(password_hash(password, self.salt), self.expected)
        return hmac.compare_digest(username.encode(), self.username) and valid_password

    def create_session(self) -> str:
        now = time.monotonic()
        self.sessions = {key: expiry for key, expiry in self.sessions.items() if expiry > now}
        session = secrets.token_urlsafe(32)
        self.sessions[session] = now + SESSION_AGE
        return session

    def authenticated(self, session: str) -> bool:
        return self.sessions.get(session, 0) > time.monotonic()

    def revoke(self, session: str) -> None:
        self.sessions.pop(session, None)
