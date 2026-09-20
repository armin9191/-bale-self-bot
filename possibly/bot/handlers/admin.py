# bot/handlers/admin.py

import logging
from typing import Optional

from bale import Bot, Message

from config import settings
from bot.messages import error, success, info
from bot.permissions import is_configured_admin, is_owner

logger = logging.getLogger("POSSIBLY.admin")


def get_user_id_from_message(message: Message) -> Optional[int]:
    """
    تلاش برای پیدا کردن user_id هدف از:
    1. Reply
    2. آرگومان عددی دستور

    اگر هیچ‌کدام وجود نداشته باشد، None برمی‌گرداند.
    """

    # Reply
    reply = getattr(message, "reply_to_message", None)

    if reply is not None:
        reply_from = getattr(reply, "author", None)

        if reply_from is not None:
            user_id = getattr(reply_from, "id", None)

            if user_id is not None:
                return int(user_id)

    # Argument
    text = getattr(message, "content", None)

    if not text:
        text = getattr(message, "text", None)

    if not text:
        return None

    parts = text.strip().split()

    if len(parts) >= 2:
        try:
            return int(parts[1])
        except ValueError:
            return None

    return None


def register_admin_handlers(bot: Bot):

    @bot.event
    async def on_message(message: Message):
        """
        مدیریت دستورات گروه.
        """

        try:
            chat = getattr(message, "chat", None)

            if chat is None:
                return

            chat_id = getattr(chat, "id", None)

            if chat_id is None:
                return

            # فقط گروه اصلی
            if int(chat_id) != settings.ALLOWED_GROUP_ID:
                return

            author = getattr(message, "author", None)

            if author is None:
                return

            author_id = getattr(author, "id", None)

            if author_id is None:
                return

            author_id = int(author_id)

            # متن پیام
            text = getattr(message, "content", None)

            if not text:
                text = getattr(message, "text", None)

            if not text:
                return

            text = text.strip()

            # فقط Owner / POSSIBLY Admin
            allowed = (
                is_owner(author_id, settings.OWNER_ID)
                or is_configured_admin(
                    author_id,
                    settings.POSSIBLY_ADMIN_ID,
                )
            )

            if not allowed:
                return

            # -------------------------
            # /ban
            # -------------------------

            if text.startswith("/ban"):
                target_id = get_user_id_from_message(message)

                if target_id is None:
                    await message.reply(
                        error(
                            "کاربر هدف مشخص نشده است.\n\n"
                            "روش استفاده:\n"
                            "/ban USER_ID\n\n"
                            "یا روی پیام کاربر Reply کنید."
                        )
                    )
                    return

                if target_id == author_id:
                    await message.reply(
                        error("نمی‌توانی خودت را بن کنی.")
                    )
                    return

                if target_id == settings.OWNER_ID:
                    await message.reply(
                        error("امکان بن کردن Owner وجود ندارد.")
                    )
                    return

                # API moderation در نسخه نصب‌شده باید در اینجا
                # با متد واقعی Bale متصل شود.
                #
                # عمداً متد حدسی صدا زده نمی‌شود.
                #
                # TODO:
                # بعد از تأیید API نسخه 2.5.0:
                # bot.ban_chat_member(...)

                await message.reply(
                    info(
                        f"درخواست Ban برای کاربر `{target_id}` دریافت شد.\n"
                        "اتصال عملیات Ban به API رسمی Bale در مرحله مدیریت "
                        "تکمیل می‌شود."
                    )
                )

                logger.info(
                    "Ban requested by %s for %s",
                    author_id,
                    target_id,
                )

                return

            # -------------------------
            # /kick
            # -------------------------

            if text.startswith("/kick"):
                target_id = get_user_id_from_message(message)

                if target_id is None:
                    await message.reply(
                        error(
                            "کاربر هدف مشخص نشده است.\n\n"
                            "روش استفاده:\n"
                            "/kick USER_ID\n\n"
                            "یا روی پیام کاربر Reply کنید."
                        )
                    )
                    return

                if target_id == author_id:
                    await message.reply(
                        error("نمی‌توانی خودت را Kick کنی.")
                    )
                    return

                if target_id == settings.OWNER_ID:
                    await message.reply(
                        error("امکان Kick کردن Owner وجود ندارد.")
                    )
                    return

                await message.reply(
                    info(
                        f"درخواست Kick برای کاربر `{target_id}` دریافت شد.\n"
                        "اتصال عملیات Kick به API رسمی Bale در مرحله "
                        "مدیریت تکمیل می‌شود."
                    )
                )

                logger.info(
                    "Kick requested by %s for %s",
                    author_id,
                    target_id,
                )

                return

            # -------------------------
            # /unban
            # -------------------------

            if text.startswith("/unban"):
                target_id = get_user_id_from_message(message)

                if target_id is None:
                    await message.reply(
                        error(
                            "کاربر هدف مشخص نشده است.\n\n"
                            "روش استفاده:\n"
                            "/unban USER_ID"
                        )
                    )
                    return

                await message.reply(
                    info(
                        f"درخواست Unban برای کاربر `{target_id}` دریافت شد.\n"
                        "اتصال عملیات Unban به API رسمی Bale در مرحله "
                        "مدیریت تکمیل می‌شود."
                    )
                )

                logger.info(
                    "Unban requested by %s for %s",
                    author_id,
                    target_id,
                )

                return

        except Exception:
            logger.exception("Admin handler failed")
