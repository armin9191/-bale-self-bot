id="v7m3qx"
# POSSIBLY
# Group administration handlers

from __future__ import annotations

import logging
import re
from typing import Any

import bale

from bot.messages import admin, error, success
from bot.permissions import can_manage_group, is_owner_or_admin
from config import settings
from database.repositories import (
    create_moderation_log,
    get_member_role,
    upsert_group_member,
    upsert_user,
)


logger = logging.getLogger("POSSIBLY.admin")


def _get_chat_id(message: Any) -> int | None:
    chat = getattr(message, "chat", None)

    if chat is None:
        return None

    chat_id = getattr(chat, "id", None)

    try:
        return int(chat_id)
    except (TypeError, ValueError):
        return None


def _get_user_id(user: Any) -> int | None:
    if user is None:
        return None

    user_id = getattr(user, "id", None)

    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def _get_message_user_id(message: Any) -> int | None:
    user = getattr(message, "author", None)

    if user is None:
        user = getattr(message, "from_user", None)

    return _get_user_id(user)


def _is_allowed_group(message: Any) -> bool:
    chat_id = _get_chat_id(message)

    return (
        chat_id is not None
        and chat_id == settings.ALLOWED_GROUP_ID
    )


def _extract_user_id_from_text(text: str) -> int | None:
    """
    /ban 123456
    /kick 123456
    /unban 123456

    همچنین username عددی را در صورت وجود استخراج می‌کند.
    """

    parts = text.strip().split(maxsplit=1)

    if len(parts) < 2:
        return None

    raw = parts[1].strip()

    match = re.search(r"\d+", raw)

    if not match:
        return None

    try:
        return int(match.group())
    except ValueError:
        return None


def _get_reply_target_id(message: Any) -> int | None:
    reply = getattr(message, "reply_to_message", None)

    if reply is None:
        reply = getattr(message, "reply_to", None)

    if reply is None:
        return None

    user = getattr(reply, "author", None)

    if user is None:
        user = getattr(reply, "from_user", None)

    return _get_user_id(user)


async def _get_target_user_id(message: Any) -> int | None:
    """
    اول Reply و بعد User ID داخل متن را بررسی می‌کند.
    """

    target_id = _get_reply_target_id(message)

    if target_id is not None:
        return target_id

    text = getattr(message, "content", None)

    if text is None:
        text = getattr(message, "text", "")

    if not isinstance(text, str):
        return None

    return _extract_user_id_from_text(text)


async def _get_sender_id(message: Any) -> int | None:
    return _get_message_user_id(message)


async def _check_admin(
    message: Any,
) -> bool:
    if not _is_allowed_group(message):
        return False

    sender_id = await _get_sender_id(message)

    if sender_id is None:
        return False

    if is_owner_or_admin(sender_id):
        return True

    role = await get_member_role(
        settings.ALLOWED_GROUP_ID,
        sender_id,
    )

    return can_manage_group(
        sender_id,
        role,
    )


async def _safe_delete(message: Any) -> bool:
    """
    حذف پیام فقط در صورتی که متد واقعی message موجود باشد.
    """

    delete_method = getattr(message, "delete", None)

    if delete_method is None:
        return False

    try:
        result = delete_method()

        if hasattr(result, "__await__"):
            await result

        return True

    except Exception:
        logger.warning(
            "Could not delete message",
            exc_info=True,
        )
        return False


async def _reply(
    message: Any,
    text: str,
) -> Any:
    reply_method = getattr(message, "reply", None)

    if reply_method is not None:
        result = reply_method(text)

        if hasattr(result, "__await__"):
            return await result

        return result

    answer_method = getattr(message, "answer", None)

    if answer_method is not None:
        result = answer_method(text)

        if hasattr(result, "__await__"):
            return await result

        return result

    return None


async def _call_ban(
    bot: bale.Bot,
    chat_id: int,
    user_id: int,
) -> bool:
    """
    تلاش برای استفاده از API واقعی نصب‌شده.

    متدهای مختلف حدس زده نمی‌شوند؛ اول API رسمی موجود
    روی Bot بررسی می‌شود.
    """

    method = getattr(bot, "ban_chat_member", None)

    if method is None:
        return False

    result = method(
        chat_id=chat_id,
        user_id=user_id,
    )

    if hasattr(result, "__await__"):
        result = await result

    return bool(result)


async def _call_unban(
    bot: bale.Bot,
    chat_id: int,
    user_id: int,
) -> bool:
    method = getattr(bot, "unban_chat_member", None)

    if method is None:
        return False

    result = method(
        chat_id=chat_id,
        user_id=user_id,
    )

    if hasattr(result, "__await__"):
        result = await result

    return bool(result)


async def _call_kick(
    bot: bale.Bot,
    chat_id: int,
    user_id: int,
) -> bool:
    """
    Kick مستقل ممکن است در API نسخه نصب‌شده وجود نداشته باشد.

    اگر ban_chat_member موجود باشد، از همان قابلیت واقعی استفاده
    می‌کنیم؛ در غیر این صورت عملیات fake انجام نمی‌شود.
    """

    return await _call_ban(
        bot,
        chat_id,
        user_id,
    )


async def ban_command(
    message: Any,
    bot: bale.Bot,
) -> None:
    if not _is_allowed_group(message):
        return

    if not await _check_admin(message):
        await _reply(
            message,
            error("شما اجازه استفاده از این دستور را ندارید."),
        )
        return

    target_id = await _get_target_user_id(message)

    if target_id is None:
        await _reply(
            message,
            error(
                "کاربر مشخص نیست.\n"
                "روی پیام کاربر Reply کنید یا:\n"
                "/ban USER_ID"
            ),
        )
        return

    if target_id == settings.OWNER_ID:
        await _reply(
            message,
            error("امکان مدیریت Owner اصلی وجود ندارد."),
        )
        return

    chat_id = _get_chat_id(message)

    if chat_id is None:
        return

    try:
        success_result = await _call_ban(
            bot,
            chat_id,
            target_id,
        )

        if not success_result:
            await _reply(
                message,
                error(
                    "API نسخه فعلی بله امکان Ban این کاربر را "
                    "در این شرایط فراهم نکرد."
                ),
            )
            return

        actor_id = await _get_sender_id(message)

        if actor_id is not None:
            await create_moderation_log(
                group_id=chat_id,
                actor_id=actor_id,
                target_id=target_id,
                action="ban",
            )

        await _reply(
            message,
            success(
                f"کاربر `{target_id}` بن شد."
            ),
        )

    except Exception:
        logger.exception(
            "Ban failed: chat=%s target=%s",
            chat_id,
            target_id,
        )

        await _reply(
            message,
            error("عملیات Ban با خطا مواجه شد."),
        )


async def unban_command(
    message: Any,
    bot: bale.Bot,
) -> None:
    if not _is_allowed_group(message):
        return

    if not await _check_admin(message):
        await _reply(
            message,
            error("شما اجازه استفاده از این دستور را ندارید."),
        )
        return

    target_id = await _get_target_user_id(message)

    if target_id is None:
        await _reply(
            message,
            error(
                "کاربر مشخص نیست.\n"
                "Reply یا /unban USER_ID استفاده کنید."
            ),
        )
        return

    chat_id = _get_chat_id(message)

    if chat_id is None:
        return

    try:
        success_result = await _call_unban(
            bot,
            chat_id,
            target_id,
        )

        if not success_result:
            await _reply(
                message,
                error(
                    "API نسخه فعلی بله امکان Unban این کاربر را "
                    "در این شرایط فراهم نکرد."
                ),
            )
            return

        actor_id = await _get_sender_id(message)

        if actor_id is not None:
            await create_moderation_log(
                group_id=chat_id,
                actor_id=actor_id,
                target_id=target_id,
                action="unban",
            )

        await _reply(
            message,
            success(
                f"محدودیت کاربر `{target_id}` برداشته شد."
            ),
        )

    except Exception:
        logger.exception(
            "Unban failed: chat=%s target=%s",
            chat_id,
            target_id,
        )

        await _reply(
            message,
            error("عملیات Unban با خطا مواجه شد."),
        )


async def kick_command(
    message: Any,
    bot: bale.Bot,
) -> None:
    if not _is_allowed_group(message):
        return

    if not await _check_admin(message):
        await _reply(
            message,
            error("شما اجازه استفاده از این دستور را ندارید."),
        )
        return

    target_id = await _get_target_user_id(message)

    if target_id is None:
        await _reply(
            message,
            error(
                "کاربر مشخص نیست.\n"
                "Reply یا /kick USER_ID استفاده کنید."
            ),
        )
        return

    chat_id = _get_chat_id(message)

    if chat_id is None:
        return

    try:
        success_result = await _call_kick(
            bot,
            chat_id,
            target_id,
        )

        if not success_result:
            await _reply(
                message,
                error(
                    "Kick مستقل توسط API فعلی قابل انجام نیست."
                ),
            )
            return

        actor_id = await _get_sender_id(message)

        if actor_id is not None:
            await create_moderation_log(
                group_id=chat_id,
                actor_id=actor_id,
                target_id=target_id,
                action="kick",
            )

        await _reply(
            message,
            success(
                f"کاربر `{target_id}` از گروه خارج شد."
            ),
        )

    except Exception:
        logger.exception(
            "Kick failed: chat=%s target=%s",
            chat_id,
            target_id,
        )

        await _reply(
            message,
            error("عملیات Kick با خطا مواجه شد."),
        )


async def register_member(
    message: Any,
) -> None:
    """
    ثبت کاربری که ربات در گروه مشاهده کرده است.
    """

    if not _is_allowed_group(message):
        return

    user = getattr(message, "author", None)

    if user is None:
        user = getattr(message, "from_user", None)

    user_id = _get_user_id(user)

    if user_id is None:
        return

    username = getattr(user, "username", None)

    first_name = getattr(user, "first_name", None)
    last_name = getattr(user, "last_name", None)

    display_name = " ".join(
        part
        for part in (
            first_name,
            last_name,
        )
        if part
    ).strip()

    if not display_name:
        display_name = (
            getattr(user, "display_name", None)
            or username
            or str(user_id)
        )

    await upsert_user(
        user_id=user_id,
        username=username,
        display_name=display_name,
    )

    role = "member"

    if user_id == settings.OWNER_ID:
        role = "owner"
    elif user_id == settings.POSSIBLY_ADMIN_ID:
        role = "admin"

    await upsert_group_member(
        group_id=settings.ALLOWED_GROUP_ID,
        user_id=user_id,
        role=role,
    )


def register_admin_handlers(
    bot: bale.Bot,
) -> None:
    """
    Handler registration.

    نکته:
    decoratorهای دقیق نسخه python-bale-bot باید مطابق API همان نسخه
    استفاده شوند. این تابع عمداً تا زمانی که registration API نسخه
    نصب‌شده تأیید نشده، decorator حدسی ایجاد نمی‌کند.
    """

    logger.info(
        "Admin handler module loaded"
    )
