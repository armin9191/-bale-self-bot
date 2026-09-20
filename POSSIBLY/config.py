"""POSSIBLY configuration — values are read directly from this file."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str = "81087490:Ks2I1Rp6kzAiTsoYSCe1W9tPn3cJRH5LWaY"
    DATABASE_URL: str = "postgresql://postgres:cMNEnLwTdcfVuREgxJEbhxqzfUtwVjvM@postgres.railway.internal:5432/railway"

    ALLOWED_GROUP_ID: int = 4739068741
    ALLOWED_GROUP_USERNAME: str = "@possibly"

    OWNER_ID: int = 1967315238
    POSSIBLY_ADMIN_ID: int = 1967315238

    MAX_LEARNED_WORDS: int = 300
    WHISPER_TTL_SECONDS: int = 600
    MAX_GIF_BYTES: int = 8 * 1024 * 1024
    MAX_GIF_FRAMES: int = 80
    MAX_GIF_DIMENSION: int = 512
    BACKUP_COOLDOWN_SECONDS: int = 180
    RATE_LIMIT_SECONDS: float = 1.2

    FONT_PATH: str = "assets/fonts/Vazirmatn-Regular.ttf"


settings = Settings()
