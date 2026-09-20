# bot/handlers/learning.py

import logging

from bale import Bot, Message

from config import settings
from bot.messages import error, success, info
from bot.permissions import is_configured_admin, is_owner
from database.postgres import get_pool

logger = logging.getLogger("POSSIBLY.learning")

MAX_LEARNED_WORDS = 300


def get_author_id(message: Message) -> int | None:
    author = getattr(message, "author", None)

    if author is None:
        return None

    user_id = getattr(author, "id", None)

    if user_id is None:
        return None

    return int(user_id)


def get_text(message: Message) -> str:
    text = getattr(message, "content", None)

    if not text:
        text = getattr(message, "text", None)

    return (text or "").strip()


def is_admin(user_id: int) -> bool:
    return (
        is_owner(user_id, settings.OWNER_ID)
        or is_configured_admin(
            user_id,
            settings.POSSIBLY_ADMIN_ID,
        )
    )


def parse_learn_command(text: str):
    """
    فرمت:

    یاد بگیر trigger response

    مثال:

    یاد بگیر سلام سلام خوبی؟

    خروجی:

    trigger = سلام
    response = سلام خوبی؟
    """

    parts = text.split(maxsplit=2)

    if len(parts) < 3:
        return None, None

    trigger = parts[2].strip()

    # برای اینکه بتوانیم trigger و response را جدا کنیم،
    # از اولین فاصله بعد از trigger استفاده می‌کنیم.
    #
    # مثال:
    # یاد بگیر تست سلام
    #
    # trigger = تست
    # response = سلام

    trigger_parts = trigger.split(maxsplit=1)

    if len(trigger_parts) < 2:
        return None, None

    return (
        trigger_parts[0].strip(),
        trigger_parts[1].strip(),
    )


async def add_learning(
    group_id: int,
    trigger: str,
    response: str,
    created_by: int,
) -> bool:

    pool = get_pool()

    count = await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM learned_words
        WHERE group_id = $1
        """,
        group_id,
    )

    if count >= MAX_LEARNED_WORDS:
        return False

    await pool.execute(
        """
        INSERT INTO learned_words (
            group_id,
            trigger,
            response,
            created_by
        )
        VALUES ($1, $2, $3, $4)

        ON CONFLICT (group_id, trigger)
        DO UPDATE SET
            response = EXCLUDED.response,
            created_by = EXCLUDED.created_by,
            created_at = NOW()
        """,
        group_id,
        trigger,
        response,
        created_by,
    )

    return True


async def remove_learning(
    group_id: int,
    trigger: str,
) -> bool:

    pool = get_pool()

    result = await pool.execute(
        """
        DELETE FROM learned_words
        WHERE group_id = $1
          AND trigger = $2
        """,
        group_id,
        trigger,
    )

    return result.endswith("1")


async def get_learnings(group_id: int):
    pool = get_pool()

    return await pool.fetch(
        """
        SELECT
            trigger,
            response
        FROM learned_words
        WHERE group_id = $1
        ORDER BY id ASC
        """,
        group_id,
    )


async def get_learning_response(
    group_id: int,
    trigger: str,
):
    pool = get_pool()

    return await pool.fetchval(
        """
        SELECT response
        FROM learned_words
        WHERE group_id = $1
          AND trigger = $2
        LIMIT 1
        """,
        group_id,
        trigger,
    )


def register_learning_handlers(bot: Bot):

    @bot.event
    async def on_message(message: Message):

        try:
            chat = getattr(message, "chat", None)

            if chat is None:
                return

            group_id = getattr(chat, "id", None)

            if group_id is None:
                return

            group_id = int(group_id)

            # فقط گروه POSSIBLY
            if group_id != settings.ALLOWED_GROUP_ID:
                return

            user_id = get_author_id(message)

            if user_id is None:
                return

            text = get_text(message)

            if not text:
                return

            # --------------------------------
            # یاد بگیر
            # --------------------------------

            if text.startswith("یاد بگیر"):

                if not is_admin(user_id):
                    await message.reply(
                        error(
                            "فقط Admin یا Owner می‌تواند "
                            "یادگیری جدید ثبت کند."
                        )
                    )
                    return

                raw = text[len("یاد بگیر"):].strip()

                parts = raw.split(maxsplit=1)

                if len(parts) < 2:
                    await message.reply(
                        error(
                            "فرمت صحیح:\n\n"
                            "یاد بگیر trigger response\n\n"
                            "مثال:\n"
                            "یاد بگیر تست سلام"
                        )
                    )
                    return

                trigger = parts[0].strip()
                response = parts[1].strip()

                if not trigger or not response:
                    await message.reply(
                        error("Trigger و پاسخ نمی‌توانند خالی باشند.")
                    )
                    return

                if len(trigger) > 100:
                    await message.reply(
                        error("Trigger بیش از حد طولانی است.")
                    )
                    return

                if len(response) > 4000:
                    await message.reply(
                        error("پاسخ بیش از حد طولانی است.")
                    )
                    return

                # بررسی وجود قبلی
                pool = get_pool()

                existing = await pool.fetchval(
                    """
                    SELECT 1
                    FROM learned_words
                    WHERE group_id = $1
                      AND trigger = $2
                    LIMIT 1
                    """,
                    group_id,
                    trigger,
                )

                if existing:
                    await pool.execute(
                        """
                        UPDATE learned_words
                        SET
                            response = $1,
                            created_by = $2,
                            created_at = NOW()
                        WHERE group_id = $3
                          AND trigger = $4
                        """,
                        response,
                        user_id,
                        group_id,
                        trigger,
                    )

                    await message.reply(
                        success(
                            f"یادگیری «{trigger}» بروزرسانی شد."
                        )
                    )

                    logger.info(
                        "Learning updated: group=%s trigger=%s by=%s",
                        group_id,
                        trigger,
                        user_id,
                    )

                    return

                count = await pool.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM learned_words
                    WHERE group_id = $1
                    """,
                    group_id,
                )

                if count >= MAX_LEARNED_WORDS:
                    await message.reply(
                        error(
                            "سقف یادگیری این گروه به ۳۰۰ مورد رسیده است."
                        )
                    )
                    return

                await pool.execute(
                    """
                    INSERT INTO learned_words (
                        group_id,
                        trigger,
                        response,
                        created_by
                    )
                    VALUES ($1, $2, $3, $4)
                    """,
                    group_id,
                    trigger,
                    response,
                    user_id,
                )

                await message.reply(
                    success(
                        f"«{trigger}» یاد گرفته شد."
                    )
                )

                logger.info(
                    "Learning added: group=%s trigger=%s by=%s",
                    group_id,
                    trigger,
                    user_id,
                )

                return

            # --------------------------------
            # فراموش کن
            # --------------------------------

            if text.startswith("فراموش کن"):

                if not is_admin(user_id):
                    await message.reply(
                        error(
                            "فقط Admin یا Owner می‌تواند "
                            "یادگیری را حذف کند."
                        )
                    )
                    return

                trigger = text[len("فراموش کن"):].strip()

                if not trigger:
                    await message.reply(
                        error(
                            "فرمت صحیح:\n\n"
                            "فراموش کن trigger"
                        )
                    )
                    return

                deleted = await remove_learning(
                    group_id,
                    trigger,
                )

                if not deleted:
                    await message.reply(
                        error(
                            f"یادگیری «{trigger}» پیدا نشد."
                        )
                    )
                    return

                await message.reply(
                    success(
                        f"یادگیری «{trigger}» فراموش شد."
                    )
                )

                logger.info(
                    "Learning removed: group=%s trigger=%s by=%s",
                    group_id,
                    trigger,
                    user_id,
                )

                return

            # --------------------------------
            # لیست یادگیری
            # --------------------------------

            if text in (
                "لیست یادگیری",
                "لیست یادگیری‌ها",
            ):

                if not is_admin(user_id):
                    await message.reply(
                        error(
                            "فقط Admin یا Owner می‌تواند "
                            "لیست یادگیری‌ها را ببیند."
                        )
                    )
                    return

                rows = await get_learnings(group_id)

                if not rows:
                    await message.reply(
                        info(
                            "هنوز چیزی برای گروه یاد گرفته نشده است."
                        )
                    )
                    return

                lines = [
                    "🧠 یادگیری‌های POSSIBLY",
                    "",
                ]

                for index, row in enumerate(rows, start=1):
                    trigger = row["trigger"]

                    lines.append(
                        f"{index}. {trigger}"
                    )

                lines.extend(
                    [
                        "",
                        f"📚 تعداد: {len(rows)}/{MAX_LEARNED_WORDS}",
                    ]
                )

                await message.reply(
                    info("\n".join(lines))
                )

                return

            # --------------------------------
            # پاسخ به trigger
            # --------------------------------

            # دستورات مدیریتی نباید به عنوان trigger بررسی شوند.
            if (
                text.startswith("/")
                or text.startswith("یاد بگیر")
                or text.startswith("فراموش کن")
                or text.startswith("لیست یادگیری")
            ):
                return

            response = await get_learning_response(
                group_id,
                text,
            )

            if response is None:
                return

            await message.reply(
                info(response)
            )

        except Exception:
            logger.exception(
                "Learning handler failed"
            )
