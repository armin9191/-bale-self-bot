# POSSIBLY
# Permission helpers

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


def is_privileged(user_id: int) -> bool:
    return (
        is_owner(user_id)
        or is_configured_admin(user_id)
    )


def role_name(role: Role) -> str:
    if role == Role.OWNER:
        return "👑 Owner"

    if role == Role.ADMIN:
        return "🛡 Admin"

    return "👤 Member"


def can_manage(user_id: int) -> bool:
    return is_privileged(user_id)


def can_manage_learning(user_id: int) -> bool:
    return is_privileged(user_id)


def can_view_admin_panel(user_id: int) -> bool:
    return is_privileged(user_id)


def can_request_backup(user_id: int) -> bool:
    return user_id == settings.POSSIBLY_ADMIN_ID
