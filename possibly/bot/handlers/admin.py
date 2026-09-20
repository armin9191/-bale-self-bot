# POSSIBLY
# Group administration

from __future__ import annotations

import logging

from bot.messages import admin as admin_message
from bot.messages import error, success
from bot.permissions import is_privileged
from database.postgres import get_pool


logger = logging.getLogger("POSSIBLY.admin")


def register(bot) -> None:
    """
    Administration handler registration point.

    Bale-specific decorators/methods will be connected only after
    verifying the installed python-bale-bot API.
    """

    logger.info("Administration handler registered")


async def log_moderation(
    group_id: int,
    actor_id: int,
    action: str,
    target_id: int | None = None,
    details: dict | None = None,
) -> None:
    pool = get_pool()

    await pool.execute(
        """
        INSERT INTO moderation_logs (
            group_id,
            actor_id,
            target_id,
            action,
            details
        )
        VALUES ($1, $2, $3, $4, $5::jsonb)
        """,
        group_id,
        actor_id,
        target_id,
        action,
        "{}" if details is None else _json(details),
    )


def _json(data: dict) -> str:
    import json

    return json.dumps(
        data,
        ensure_ascii=False,
    )


def check_management_permission(
    user_id: int,
) -> bool:
    return is_privileged(user_id)


def permission_denied() -> str:
    return error(
        "شما اجازه انجام این عملیات را ندارید."
    )


def invalid_target() -> str:
    return error(
        "کاربر هدف معتبر نیست."
    )


def management_help() -> str:
    return admin_message(
        "دستورات مدیریت:\n\n"
        "/ban USER_ID\n"
        "/kick USER_ID\n"
        "/unban USER_ID\n\n"
        "یا در صورت پشتیبانی API، "
        "دستور را روی پیام کاربر Reply کنید."
    )


async def moderation_success(
    group_id: int,
    actor_id: int,
    action: str,
    target_id: int,
) -> str:
    await log_moderation(
        group_id=group_id,
        actor_id=actor_id,
        target_id=target_id,
        action=action,
    )

    logger.info(
        "Moderation action=%s group=%s actor=%s target=%s",
        action,
        group_id,
        actor_id,
        target_id,
    )

    return success(
        f"عملیات {action} برای کاربر "
        f"`{target_id}` ثبت شد."
    )
