# POSSIBLY
# Python 3.12+

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str
    DATABASE_URL: str
    ALLOWED_GROUP_ID: int
    ALLOWED_GROUP_USERNAME: str
    OWNER_ID: int
    POSSIBLY_ADMIN_ID: int


settings = Settings(
    # توکن ربات بله
    BOT_TOKEN="1266619413:auADLARdWSeTJQaA9dxuUc01oxee7L_BsNo",

    # آدرس PostgreSQL
    DATABASE_URL="postgresql://postgres:cMNEnLwTdcfVuREgxJEbhxqzfUtwVjvM@postgres.railway.internal:5432/railway",

    # آیدی عددی گروه اصلی POSSIBLY
    ALLOWED_GROUP_ID=4739068741,

    # یوزرنیم گروه
    ALLOWED_GROUP_USERNAME="@possibly",

    # Owner اصلی
    OWNER_ID=1967315238,

    # ادمین اختصاصی POSSIBLY
    # امکان دریافت بکاپ از طریق Private Chat
    POSSIBLY_ADMIN_ID=1967315238,
)