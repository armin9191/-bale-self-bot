# POSSIBLY
# Permission system

from __future__ import annotations

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


def is_owner_or_admin(user_id: int) -> bool:
    return is_owner(user_id) or is_configured_admin(user_id)


def role_from_database(role: str | None) -> Role:
    if not role:
        return Role.MEMBER

    normalized = role.lower().strip()

    if normalized == Role.OWNER:
        return Role.OWNER

    if normalized == Role.ADMIN:
        return Role.ADMIN

    return Role.MEMBER


def can_manage_group(
    user_id: int,
    role: str | None = None,
) -> bool:
    """
    دسترسی مدیریتی.

    Owner و POSSIBLY_ADMIN همیشه دسترسی مدیریتی دارند.
    برای سایر کاربران، role ذخیره‌شده در دیتابیس بررسی می‌شود.
    """
    if is_owner_or_admin(user_id):
        return True

    return role_from_database(role) in {
        Role.OWNER,
        Role.ADMIN,
    }


def can_use_learning(
    user_id: int,
    role: str | None = None,
) -> bool:
    return can_manage_group(user_id, role)


def can_view_admin_panel(
    user_id: int,
    role: str | None = None,
) -> bool:
    return can_manage_group(user_id, role)


def can_backup(user_id: int) -> bool:
    """
    بکاپ PostgreSQL فقط برای ادمین اختصاصی POSSIBLY.
    """
    return user_id == settings.POSSIBLY_ADMIN_ID


def display_role(role: Role) -> str:
    if role == Role.OWNER:
        return "👑 Owner"

    if role == Role.ADMIN:
        return "🛡 Admin"

    return "👤 Member"

