"""Repository layer — no raw SQL in handlers."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from database.postgres import get_pool


async def upsert_user(user_id: int, username: Optional[str], display_name: str) -> None:
    await get_pool().execute(
        """
        INSERT INTO users (user_id, username, display_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO UPDATE
        SET username = EXCLUDED.username,
            display_name = EXCLUDED.display_name,
            last_seen = NOW()
        """,
        user_id,
        username,
        display_name or str(user_id),
    )


async def upsert_member(group_id: int, user_id: int, role: str = "member") -> None:
    await get_pool().execute(
        """
        INSERT INTO group_members (group_id, user_id, role)
        VALUES ($1, $2, $3)
        ON CONFLICT (group_id, user_id) DO UPDATE SET role = EXCLUDED.role
        """,
        group_id,
        user_id,
        role,
    )


async def increment_stat(group_id: int, user_id: int, stat: str, day: date) -> None:
    allowed = {"messages", "gifs", "voice", "photos", "videos", "other"}
    if stat not in allowed:
        raise ValueError(f"invalid stat: {stat}")
    await get_pool().execute(
        f"""
        INSERT INTO daily_stats (group_id, user_id, date, {stat})
        VALUES ($1, $2, $3, 1)
        ON CONFLICT (group_id, user_id, date)
        DO UPDATE SET {stat} = daily_stats.{stat} + 1
        """,
        group_id,
        user_id,
        day,
    )


async def get_today_totals(group_id: int, day: date) -> dict[str, int]:
    row = await get_pool().fetchrow(
        """
        SELECT
            COALESCE(SUM(messages), 0) AS messages,
            COALESCE(SUM(gifs), 0) AS gifs,
            COALESCE(SUM(voice), 0) AS voice,
            COALESCE(SUM(photos), 0) AS photos,
            COALESCE(SUM(videos), 0) AS videos,
            COALESCE(SUM(other), 0) AS other
        FROM daily_stats
        WHERE group_id = $1 AND date = $2
        """,
        group_id,
        day,
    )
    return dict(row) if row else {}


async def get_top_users(group_id: int, day: date, limit: int = 3) -> list[dict[str, Any]]:
    rows = await get_pool().fetch(
        """
        SELECT u.username, u.display_name, ds.messages, ds.user_id
        FROM daily_stats ds
        LEFT JOIN users u ON u.user_id = ds.user_id
        WHERE ds.group_id = $1 AND ds.date = $2
        ORDER BY ds.messages DESC
        LIMIT $3
        """,
        group_id,
        day,
        limit,
    )
    return [dict(r) for r in rows]


async def count_learned(group_id: int) -> int:
    return await get_pool().fetchval(
        "SELECT COUNT(*) FROM learned_words WHERE group_id = $1", group_id
    ) or 0


async def set_learned(group_id: int, trigger: str, response: str, created_by: int) -> None:
    await get_pool().execute(
        """
        INSERT INTO learned_words (group_id, trigger, response, created_by)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (group_id, trigger) DO UPDATE
        SET response = EXCLUDED.response,
            created_by = EXCLUDED.created_by,
            created_at = NOW()
        """,
        group_id,
        trigger,
        response,
        created_by,
    )


async def delete_learned(group_id: int, trigger: str) -> bool:
    result = await get_pool().execute(
        "DELETE FROM learned_words WHERE group_id = $1 AND trigger = $2",
        group_id,
        trigger,
    )
    return result.endswith("1")


async def list_learned_triggers(group_id: int) -> list[str]:
    rows = await get_pool().fetch(
        "SELECT trigger FROM learned_words WHERE group_id = $1 ORDER BY id",
        group_id,
    )
    return [r["trigger"] for r in rows]


async def get_learned_response(group_id: int, trigger: str) -> Optional[str]:
    return await get_pool().fetchval(
        "SELECT response FROM learned_words WHERE group_id = $1 AND trigger = $2",
        group_id,
        trigger,
    )


async def log_moderation(
    group_id: int,
    actor_id: int,
    target_id: Optional[int],
    action: str,
    details: Optional[dict] = None,
) -> None:
    import json
    await get_pool().execute(
        """
        INSERT INTO moderation_logs (group_id, actor_id, target_id, action, details)
        VALUES ($1, $2, $3, $4, $5::jsonb)
        """,
        group_id,
        actor_id,
        target_id,
        action,
        json.dumps(details or {}),
    )


async def create_whisper(
    group_id: int,
    sender_id: int,
    receiver_id: int,
    content: str,
    ttl_seconds: int,
) -> int:
    expires = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    return await get_pool().fetchval(
        """
        INSERT INTO whispers (group_id, sender_id, receiver_id, encrypted_or_private_content, expires_at)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        group_id,
        sender_id,
        receiver_id,
        content,
        expires,
    )


async def get_whisper(whisper_id: int) -> Optional[dict[str, Any]]:
    row = await get_pool().fetchrow(
        "SELECT * FROM whispers WHERE id = $1", whisper_id
    )
    return dict(row) if row else None


async def mark_whisper_viewed(whisper_id: int) -> None:
    await get_pool().execute(
        "UPDATE whispers SET viewed = TRUE WHERE id = $1", whisper_id
    )


async def list_group_members_seen(group_id: int, limit: int = 50) -> list[dict[str, Any]]:
    rows = await get_pool().fetch(
        """
        SELECT gm.user_id, gm.role, u.username, u.display_name
        FROM group_members gm
        LEFT JOIN users u ON u.user_id = gm.user_id
        WHERE gm.group_id = $1
        ORDER BY gm.joined_at DESC
        LIMIT $2
        """,
        group_id,
        limit,
    )
    return [dict(r) for r in rows]


async def save_game(
    game_id: UUID,
    group_id: int,
    game_type: str,
    creator_id: int,
    status: str,
    state: dict,
) -> None:
    import json
    await get_pool().execute(
        """
        INSERT INTO games (game_id, group_id, type, creator_id, status, state)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
        ON CONFLICT (game_id) DO UPDATE
        SET status = EXCLUDED.status,
            state = EXCLUDED.state,
            updated_at = NOW()
        """,
        game_id,
        group_id,
        game_type,
        creator_id,
        status,
        json.dumps(state),
    )


async def load_game(game_id: UUID) -> Optional[dict[str, Any]]:
    row = await get_pool().fetchrow("SELECT * FROM games WHERE game_id = $1", game_id)
    return dict(row) if row else None
