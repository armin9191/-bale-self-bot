# POSSIBLY
# Python 3.12+

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # ============================================================
    # Bale Bot
    # ============================================================

    BOT_TOKEN: str = (
        "1266619413:auADLARw9eTJbWSeTJQaA9dxuUc01oxee7L_BsNo"
    )

    # ============================================================
    # PostgreSQL
    # ============================================================
    #
    # این آدرس Railway Internal است.
    # برای اجرای Bot داخل Railway مناسب است.
    #
    # برای اجرای Local روی Windows باید بعداً Public DB URL
    # را جایگزین کنیم.
    #

    DATABASE_URL: str = (
        "postgresql://postgres:"
        "cMNEnLwTdcfVuREgxJEbhxqzfUtwVjvM"
        "@postgres.railway.internal:5432/railway"
    )

    # ============================================================
    # Main Group
    # ============================================================

    ALLOWED_GROUP_ID: int = 4739068741

    ALLOWED_GROUP_USERNAME: str = "@possibly"

    # ============================================================
    # Permissions
    # ============================================================

    # Owner اصلی
    OWNER_ID: int = 1967315238

    # Admin اختصاصی POSSIBLY
    # این کاربر می‌تواند از Private Chat درخواست Backup کند.
    POSSIBLY_ADMIN_ID: int = 1967315238

    # ============================================================
    # Limits / Safety
    # ============================================================

    # حداکثر تعداد یادگیری برای هر گروه
    MAX_LEARNED_WORDS: int = 300

    # حداکثر نجوا در دقیقه برای هر کاربر
    MAX_WHISPERS_PER_MINUTE: int = 5

    # حداکثر حجم GIF
    MAX_GIF_SIZE_MB: int = 10

    # حداکثر تعداد فریم GIF متحرک
    MAX_GIF_FRAMES: int = 80

    # Timeout بازی‌ها
    GAME_TIMEOUT_SECONDS: int = 1800

    # ============================================================
    # Backup
    # ============================================================

    # فقط این User ID اجازه دریافت Backup دارد.
    BACKUP_ADMIN_ID: int = 1967315238

    # نام فایل Backup
    BACKUP_FILENAME_PREFIX: str = "possibly_backup"


settings = Settings()
