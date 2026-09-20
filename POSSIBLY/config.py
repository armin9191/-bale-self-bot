from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str = "1266619413:auADLARdWSeTJQaA9dxuUc01oxee7L_BsNo"
    DATABASE_URL: str = "postgresql://postgres:cMNEnLwTdcfVuREgxJEbhxqzfUtwVjvM@postgres.railway.internal:5432/railway"
    ALLOWED_GROUP_ID: int = 4739068741
    ALLOWED_GROUP_USERNAME: str = "@possibly"
    OWNER_ID: int = 1967315238
    POSSIBLY_ADMIN_ID: int = 1967315238
    MAX_LEARNED_WORDS: int = 300
    WHISPER_TTL_SECONDS: int = 300
    MAX_GIF_BYTES: int = 8 * 1024 * 1024
    MAX_GIF_FRAMES: int = 80

settings = Settings()
