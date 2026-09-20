"""PostgreSQL connection pool and schema initialization for POSSIBLY."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import asyncpg

from config import settings

log = logging.getLogger("POSSIBLY.db")

_pool: Optional[asyncpg.Pool] = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    display_name TEXT NOT NULL DEFAULT '',
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_members (
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (group_id, user_id)
);

CREATE TABLE IF NOT EXISTS learned_words (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL,
    trigger TEXT NOT NULL,
    response TEXT NOT NULL,
    created_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (group_id, trigger)
);

CREATE TABLE IF NOT EXISTS daily_stats (
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    date DATE NOT NULL,
    messages INTEGER NOT NULL DEFAULT 0,
    gifs INTEGER NOT NULL DEFAULT 0,
    voice INTEGER NOT NULL DEFAULT 0,
    photos INTEGER NOT NULL DEFAULT 0,
    videos INTEGER NOT NULL DEFAULT 0,
    other INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (group_id, user_id, date)
);

CREATE TABLE IF NOT EXISTS games (
    game_id UUID PRIMARY KEY,
    group_id BIGINT NOT NULL,
    type TEXT NOT NULL,
    creator_id BIGINT NOT NULL,
    status TEXT NOT NULL,
    state JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS game_players (
    game_id UUID NOT NULL,
    user_id BIGINT NOT NULL,
    state JSONB NOT NULL DEFAULT '{}'::jsonb,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (game_id, user_id)
);

CREATE TABLE IF NOT EXISTS whispers (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL,
    sender_id BIGINT NOT NULL,
    receiver_id BIGINT NOT NULL,
    encrypted_or_private_content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    viewed BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS moderation_logs (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL,
    actor_id BIGINT NOT NULL,
    target_id BIGINT,
    action TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


async def init_db(max_retries: int = 5) -> asyncpg.Pool:
    """Create pool, run schema, with limited retry for transient errors."""
    global _pool
    if _pool is not None:
        return _pool

    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            _pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=1,
                max_size=10,
                command_timeout=30,
            )
            async with _pool.acquire() as con:
                await con.execute(SCHEMA)
            log.info("PostgreSQL connected and schema ready")
            return _pool
        except Exception as e:
            last_exc = e
            wait = 2 ** attempt
            log.warning("PostgreSQL connect attempt %s failed: %s — retry in %ss", attempt + 1, e, wait)
            await asyncio.sleep(wait)

    raise RuntimeError(f"Could not connect to PostgreSQL after {max_retries} attempts") from last_exc


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("PostgreSQL pool is not initialized. Call init_db() first.")
    return _pool


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        log.info("PostgreSQL pool closed")
