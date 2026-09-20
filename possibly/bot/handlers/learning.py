# POSSIBLY
# Learning system

from __future__ import annotations

import logging

from bot.messages import learning, error, success
from bot.permissions import is_privileged
from database.postgres import get_pool
from database.repositories import count_learned_words


logger = logging.getLogger("POSSIBLY.learning")

MAX_LEARNED_WORDS = 300


def register(bot) -> None:
    logger.info("Learning handler registered")


async def add_learning(
    group_id: int,
    user_id: int,
    trigger: str,
    response: str,
) -> str:
    if not is_privileged(user_id):
        return error(
            "فقط Admin یا Owner می‌تواند چیزی یاد بدهد."
        )

    trigger = trigger.strip()
    response = response.strip()

    if not trigger:
        return error(
            "Trigger نمی‌تواند خالی باشد."
        )

    if not response:
        return error(
            "پاسخ نمی‌تواند خالی باشد."
        )

    if len(trigger) > 100:
        return error(
            "Trigger بیش از حد طولانی است."
        )

    if len(response) > 4000:
        return error(
            "پاسخ بیش از حد طولانی است."
        )

    count = await count_learned_words(group_id)

    pool = get_pool()

    existing = await pool.fetchval(
        """
        SELECT 1
        FROM learned_words
        WHERE
            group_id = $1
            AND trigger = $2
        """,
        group_id,
        trigger,
    )

    if existing is None and count >= MAX_LEARNED_WORDS:
        return error(
            f"ظرفیت یادگیری گروه پر شده است.\n"
            f"حداکثر: {MAX_LEARNED_WORDS}"
        )

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
        user_id,
    )

    logger.info(
        "Learning added: group=%s trigger=%r by=%s",
        group_id,
        trigger,
        user_id,
    )

    return success(
        f"یاد گرفتم:\n\n"
        f"🔹 {trigger}\n"
        f"🔸 {response}"
    )


async def forget_learning(
    group_id: int,
    user_id: int,
    trigger: str,
) -> str:
    if not is_privileged(user_id):
        return error(
            "فقط Admin یا Owner می‌تواند یادگیری را حذف کند."
        )

    trigger = trigger.strip()

    if not trigger:
        return error(
            "Trigger را وارد کن."
        )

    pool = get_pool()

    deleted = await pool.fetchval(
        """
        DELETE FROM learned_words
        WHERE
            group_id = $1
            AND trigger = $2
        RETURNING id
        """,
        group_id,
        trigger,
    )

    if deleted is None:
        return error(
            f"چیزی با Trigger «{trigger}» پیدا نشد."
        )

    logger.info(
        "Learning removed: group=%s trigger=%r by=%s",
        group_id,
        trigger,
        user_id,
    )

    return success(
        f"«{trigger}» فراموش شد."
    )


async def get_learning(
    group_id: int,
    trigger: str,
) -> str | None:
    trigger = trigger.strip()

    if not trigger:
        return None

    pool = get_pool()

    return await pool.fetchval(
        """
        SELECT response
        FROM learned_words
        WHERE
            group_id = $1
            AND trigger = $2
        """,
        group_id,
        trigger,
    )


async def list_learning(
    group_id: int,
    user_id: int,
) -> str:
    if not is_privileged(user_id):
        return error(
            "فقط Admin یا Owner می‌تواند لیست یادگیری را ببیند."
        )

    pool = get_pool()

    rows = await pool.fetch(
        """
        SELECT
            trigger,
            response
        FROM learned_words
        WHERE group_id = $1
        ORDER BY id ASC
        LIMIT $2
        """,
        group_id,
        MAX_LEARNED_WORDS,
    )

    if not rows:
        return learning(
            "هنوز چیزی یاد نگرفتم."
        )

    lines = [
        f"تعداد یادگیری‌ها: {len(rows)}/{MAX_LEARNED_WORDS}",
        "",
    ]

    for index, row in enumerate(rows, start=1):
        response = row["response"]

        if len(response) > 100:
            response = response[:100] + "..."

        lines.append(
            f"{index}. {row['trigger']} → {response}"
        )

    return learning(
        "\n".join(lines)
    )
