# POSSIBLY
# Python 3.12+

import logging

from bale import Bot, Message

from config import settings
from bot.messages import message


logger = logging.getLogger("POSSIBLY.handlers")


# ============================================================
# Group Check
# ============================================================

def is_allowed_group(message_obj: Message) -> bool:
    """
    بررسی می‌کند پیام از گروه اصلی POSSIBLY آمده باشد.

    Private Chat برای تست /start مجاز است.
    """

    chat = getattr(message_obj, "chat", None)

    if chat is None:
        return False

    chat_id = getattr(chat, "id", None)

    # گروه اصلی
    if chat_id == settings.ALLOWED_GROUP_ID:
        return True

    # Private Chat
    chat_type = getattr(chat, "type", None)

    if str(chat_type).lower() in {
        "private",
        "privatechat",
        "private_chat",
    }:
        return True

    return False


# ============================================================
# Start
# ============================================================

async def handle_start(message_obj: Message):
    """
    /start
    """

    await message_obj.reply(
        message(
            "⚔️ ربات POSSIBLY با موفقیت آنلاین است.\n\n"
            "نسخه آزمایشی سیستم مدیریت گروه و بازی‌ها فعال شد."
        )
    )


# ============================================================
# Simple Ping
# ============================================================

async def handle_ping(message_obj: Message):
    """
    تست اتصال ربات.
    """

    await message_obj.reply(
        message(
            "🏓 Pong!\n\n"
            "POSSIBLY آنلاین است."
        )
    )


# ============================================================
# Main Message Handler
# ============================================================

async def handle_message(message_obj: Message):
    """
    Handler اصلی پیام‌ها.

    فعلاً فقط دستورات تست را مدیریت می‌کند.
    قابلیت‌های اصلی در Handlerهای جداگانه اضافه خواهند شد.
    """

    if not is_allowed_group(message_obj):
        # در Private Chat /start و ping مجاز هستند.
        chat = getattr(message_obj, "chat", None)
        chat_type = getattr(chat, "type", None)

        if str(chat_type).lower() not in {
            "private",
            "privatechat",
            "private_chat",
        }:
            return

    text = getattr(message_obj, "text", None)

    if not text:
        return

    text = text.strip()

    # --------------------------------------------------------
    # /start
    # --------------------------------------------------------

    if text == "/start":
        await handle_start(message_obj)
        return

    # --------------------------------------------------------
    # ping
    # --------------------------------------------------------

    if text.lower() in {
        "ping",
        "/ping",
    }:
        await handle_ping(message_obj)
        return


# ============================================================
# Registration
# ============================================================

def register_handlers(bot: Bot) -> None:
    """
    ثبت Handlerهای POSSIBLY روی Bale Bot.

    اینجا از event رسمی Message استفاده می‌کنیم.
    """

    @bot.event
    async def on_message(message_obj: Message):
        try:
            await handle_message(message_obj)

        except Exception:
            logger.exception(
                "Error while processing message"
            )

    logger.info("Message handler registered")
