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


def is_privileged(user_id: int) -> bool:
    return (
        is_owner(user_id)
        or is_configured_admin(user_id)
    )


def role_for_user(user_id: int) -> Role:
    if is_owner(user_id):
        return Role.OWNER

    if is_configured_admin(user_id):
        return Role.ADMIN

    return Role.MEMBER
