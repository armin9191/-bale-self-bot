from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str = "PUT_NEW_BALE_TOKEN_HERE"
    DATABASE_URL: str = "PUT_RAILWAY_PUBLIC_DATABASE_URL_HERE"
    ALLOWED_GROUP_ID: int = 4739068741
    ALLOWED_GROUP_USERNAME: str = "@possibly"
    OWNER_ID: int = 1967315238
    POSSIBLY_ADMIN_ID: int = 1967315238
    MAX_LEARNED_WORDS: int = 300
    WHISPER_TTL_SECONDS: int = 300
    MAX_GIF_BYTES: int = 8 * 1024 * 1024
    MAX_GIF_FRAMES: int = 80

settings = Settings()
