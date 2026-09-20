from enum import StrEnum
from config import settings

class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

def is_configured_admin(user_id: int) -> bool:
    return user_id == settings.POSSIBLY_ADMIN_ID

def is_owner(user_id: int) -> bool:
    return user_id == settings.OWNER_ID

def is_special_admin(user_id: int) -> bool:
    return is_owner(user_id) or is_configured_admin(user_id)

async def live_role(bot, user_id: int) -> Role:
    if is_owner(user_id):
        return Role.OWNER
    if is_configured_admin(user_id):
        return Role.ADMIN
    try:
        member = await bot.get_chat_member(settings.ALLOWED_GROUP_ID, user_id)
        status = str(getattr(member, "status", "")).lower()
        if "owner" in status or "creator" in status:
            return Role.OWNER
        if "admin" in status:
            return Role.ADMIN
    except Exception:
        pass
    return Role.MEMBER
