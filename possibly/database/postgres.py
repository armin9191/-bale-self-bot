# POSSIBLY
# PostgreSQL connection pool + schema

from __future__ import annotations

import logging

import asyncpg

from config import settings


logger = logging.getLogger("POSSIBLY.database")

_pool: asyncpg.Pool | None = None


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

    PRIMARY KEY (game_id, user_id),

    CONSTRAINT fk_game_players_game
        FOREIGN KEY (game_id)
        REFERENCES games(game_id)
        ON DELETE CASCADE
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

CREATE INDEX IF NOT EXISTS idx_group_members_group
    ON group_members(group_id);

CREATE INDEX IF NOT EXISTS idx_learned_words_group
    ON learned_words(group_id);

CREATE INDEX IF NOT EXISTS idx_daily_stats_group_date
    ON daily_stats(group_id, date);

CREATE INDEX IF NOT EXISTS idx_games_group_status
    ON games(group_id, status);

CREATE INDEX IF NOT EXISTS idx_game_players_game
    ON game_players(game_id);

CREATE INDEX IF NOT EXISTS idx_whispers_receiver
    ON whispers(receiver_id);

CREATE INDEX IF NOT EXISTS idx_whispers_expiry
    ON whispers(expires_at);

CREATE INDEX IF NOT EXISTS idx_moderation_logs_group
    ON moderation_logs(group_id);
"""


async def init_db() -> asyncpg.Pool:
    """
    PostgreSQL connection pool را ایجاد می‌کند و schema را آماده می‌کند.
    """

    global _pool

    if _pool is not None:
        return _pool

    logger.info("Connecting to PostgreSQL")

    _pool = await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=1,
        max_size=10,
        command_timeout=30,
        timeout=30,
    )

    try:
        async with _pool.acquire() as connection:
            await connection.execute(SCHEMA)

        logger.info("Connected to PostgreSQL")
        logger.info("Database schema verified")

    except Exception:
        logger.exception("Failed to initialize PostgreSQL")

        await _pool.close()
        _pool = None

        raise

    return _pool


def get_pool() -> asyncpg.Pool:
    """
    Pool آماده PostgreSQL را برمی‌گرداند.
    """

    if _pool is None:
        raise RuntimeError(
            "PostgreSQL pool has not been initialized."
        )

    return _pool


async def close_db() -> None:
    """
    Connection pool را به شکل امن می‌بندد.
    """

    global _pool

    if _pool is None:
        return

    pool = _pool
    _pool = None

    try:
        await pool.close()
        logger.info("PostgreSQL connection pool closed")

    except Exception:
        logger.exception(
            "Failed to close PostgreSQL connection pool"
        )
