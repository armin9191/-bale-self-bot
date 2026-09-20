from enum import StrEnum


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


def is_configured_admin(user_id: int, configured_admin_id: int) -> bool:
    return user_id == configured_admin_id


def is_owner(user_id: int, owner_id: int) -> bool:
    return user_id == owner_id
