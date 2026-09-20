# POSSIBLY
# Whisper system

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from bot.messages import error, success, message
from database.postgres import get_pool


logger = logging.getLogger("POSSIBLY.whisper")


WHISPER_EXPIRE_MINUTES = 10
MAX_WHISPERS_PER_MINUTE = 5


def register(bot) -> None:
    logger.info("Whisper handler registered")


async def create_whisper(
    group_id: int,
    sender_id: int,
    receiver_id: int,
    content: str,
) -> str:
    content = content.strip()

    if not content:
        return error(
            "متن نجوا نمی‌تواند خالی باشد."
        )

    if len(content) > 2000:
        return error(
            "متن نجوا نمی‌تواند بیشتر از ۲۰۰۰ کاراکتر باشد."
        )

    if sender_id == receiver_id:
        return error(
            "نمی‌توانی برای خودت نجوا بفرستی."
        )

    if not await _rate_limit_ok(
        group_id=group_id,
        sender_id=sender_id,
    ):
        return error(
            "تعداد نجواها زیاد است. کمی بعد دوباره تلاش کن."
        )

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=WHISPER_EXPIRE_MINUTES)
    )

    pool = get_pool()

    whisper_id = await pool.fetchval(
        """
        INSERT INTO whispers (
            group_id,
            sender_id,
            receiver_id,
            encrypted_or_private_content,
            expires_at
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        group_id,
        sender_id,
        receiver_id,
        content,
        expires_at,
    )

    logger.info(
        "Whisper created: id=%s group=%s sender=%s receiver=%s",
        whisper_id,
        group_id,
        sender_id,
        receiver_id,
    )

    return success(
        "نجوا با موفقیت ثبت شد.\n"
        "محتوا فقط باید از طریق یک interaction خصوصی "
        "پشتیبانی‌شده توسط API نمایش داده شود."
    )


async def get_whisper_for_receiver(
    whisper_id: int,
    receiver_id: int,
) -> str | None:
    pool = get_pool()

    row = await pool.fetchrow(
        """
        SELECT
            encrypted_or_private_content,
            expires_at,
            viewed
        FROM whispers
        WHERE
            id = $1
            AND receiver_id = $2
        """,
        whisper_id,
        receiver_id,
    )

    if row is None:
        return None

    expires_at = row["expires_at"]

    if (
        expires_at is not None
        and expires_at <= datetime.now(timezone.utc)
    ):
        return None

    if row["viewed"]:
        return None

    await pool.execute(
        """
        UPDATE whispers
        SET viewed = TRUE
        WHERE
            id = $1
            AND receiver_id = $2
        """,
        whisper_id,
        receiver_id,
    )

    return row["encrypted_or_private_content"]


async def _rate_limit_ok(
    group_id: int,
    sender_id: int,
) -> bool:
    pool = get_pool()

    result = await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM whispers
        WHERE
            group_id = $1
            AND sender_id = $2
            AND created_at >= NOW() - INTERVAL '1 minute'
        """,
        group_id,
        sender_id,
    )

    return int(result or 0) < MAX_WHISPERS_PER_MINUTE


async def cleanup_expired_whispers() -> None:
    pool = get_pool()

    await pool.execute(
        """
        DELETE FROM whispers
        WHERE
            expires_at IS NOT NULL
            AND expires_at <= NOW()
        """
    )
