"""Hashing de senhas - compatível com Django (PBKDF2) para usuários legados.

Django armazena no formato:
  pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>

Usamos hash manual do Django para verificação e geração (100% compatível).
"""

from __future__ import annotations

import base64
import hashlib
import os

_DJANGO_ITERATIONS = 600_000


def _b64encode(b: bytes) -> str:
    """Base64 encode sem trailing '=' (formato Django)."""
    return base64.b64encode(b).decode("ascii").rstrip("=")


def _b64decode_padded(s: str) -> bytes:
    """Base64 decode com padding automático (Django remove trailing '=')."""
    s = s.rstrip("=")
    padding = 4 - (len(s) % 4)
    if padding != 4:
        s += "=" * padding
    return base64.b64decode(s)


def _parse_django_hash(hashed: str) -> tuple[int, bytes, bytes] | None:
    """Retorna (iterations, salt, expected_hash) ou None se não for formato Django."""
    try:
        parts = hashed.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return None
        return int(parts[1]), _b64decode_padded(parts[2]), _b64decode_padded(parts[3])
    except Exception:
        return None


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica senha contra hash Django pbkdf2_sha256."""
    parsed = _parse_django_hash(hashed)
    if parsed is None:
        return False
    iterations, salt, expected = parsed
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, iterations)
    return dk == expected


def hash_password(plain: str) -> str:
    """Gera hash pbkdf2_sha256 no formato Django."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, _DJANGO_ITERATIONS)
    return f"pbkdf2_sha256${_DJANGO_ITERATIONS}${_b64encode(salt)}${_b64encode(dk)}"
