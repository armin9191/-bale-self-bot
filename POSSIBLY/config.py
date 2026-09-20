"""
POSSIBLY configuration.

IMPORTANT:
- Never commit real BOT_TOKEN or DATABASE_URL to GitHub.
- For local development you may temporarily put values here.
- For Railway / production: set environment variables and leave placeholders.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _env_int(key: str, default: int) -> int:
    raw = _env(key)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # Secrets — prefer environment variables (Railway Variables)
    BOT_TOKEN: str = _env("BOT_TOKEN", "REPLACE_WITH_YOUR_BOT_TOKEN")
    DATABASE_URL: str = _env(
        "DATABASE_URL",
        "postgresql://USER:PASSWORD@HOST:5432/DBNAME",
    )

    # Group restriction
    ALLOWED_GROUP_ID: int = _env_int("ALLOWED_GROUP_ID", 4739068741)
    ALLOWED_GROUP_USERNAME: str = _env("ALLOWED_GROUP_USERNAME", "@possibly")

    # Roles (User ID is the only trusted identifier)
    OWNER_ID: int = _env_int("OWNER_ID", 1967315238)
    POSSIBLY_ADMIN_ID: int = _env_int("POSSIBLY_ADMIN_ID", 1967315238)

    # Limits
    MAX_LEARNED_WORDS: int = 300
    WHISPER_TTL_SECONDS: int = 600          # 10 minutes
    MAX_GIF_BYTES: int = 8 * 1024 * 1024    # 8 MB
    MAX_GIF_FRAMES: int = 80
    MAX_GIF_DIMENSION: int = 512
    BACKUP_COOLDOWN_SECONDS: int = 300
    RATE_LIMIT_SECONDS: float = 1.5


settings = Settings()
