"""PostgreSQL pool + schema."""
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
CREATE TABLE IF NOT EXISTS group_locks (
    group_id BIGINT NOT NULL,
    lock_key TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by BIGINT,
    PRIMARY KEY (group_id, lock_key)
);
CREATE TABLE IF NOT EXISTS group_settings (

    group_id BIGINT PRIMARY KEY,
    rules_text TEXT,
    welcome_text TEXT,
    farewell_text TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by BIGINT
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

CREATE TABLE IF NOT EXISTS special_users (
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    granted_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (group_id, user_id)
);
CREATE TABLE IF NOT EXISTS user_titles (
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    set_by BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (group_id, user_id)
);
CREATE TABLE IF NOT EXISTS asl_profiles (
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    likes INTEGER NOT NULL DEFAULT 0,
    views INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by BIGINT,
    PRIMARY KEY (group_id, user_id)
);
CREATE TABLE IF NOT EXISTS asl_likes (
    group_id BIGINT NOT NULL,
    target_id BIGINT NOT NULL,
    liker_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (group_id, target_id, liker_id)
);
CREATE TABLE IF NOT EXISTS asl_history (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS user_warnings (
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (group_id, user_id)
);
CREATE TABLE IF NOT EXISTS user_mutes (
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    until_ts TIMESTAMPTZ,
    muted_by BIGINT,
    PRIMARY KEY (group_id, user_id)
);
CREATE TABLE IF NOT EXISTS user_protection (
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT TRUE,
    set_by BIGINT,
    PRIMARY KEY (group_id, user_id)
);
CREATE TABLE IF NOT EXISTS user_personal_locks (
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    lock_key TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'default',
    PRIMARY KEY (group_id, user_id, lock_key)
);
CREATE TABLE IF NOT EXISTS bot_managers (
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    granted_by BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (group_id, user_id)
);
CREATE TABLE IF NOT EXISTS force_join (
    group_id BIGINT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    set_by BIGINT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_lock_state (
    group_id BIGINT PRIMARY KEY,
    locked BOOLEAN NOT NULL DEFAULT FALSE,
    until_ts TIMESTAMPTZ,
    daily_start TEXT,
    daily_end TEXT,
    set_by BIGINT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS mute_records (
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    until_ts TIMESTAMPTZ,
    reason TEXT,
    muted_by BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (group_id, user_id)
);
CREATE TABLE IF NOT EXISTS warn_settings (
    group_id BIGINT PRIMARY KEY,
    max_warns INTEGER NOT NULL DEFAULT 3,
    action TEXT NOT NULL DEFAULT 'kick',
    updated_by BIGINT
);
CREATE TABLE IF NOT EXISTS warn_records (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    reason TEXT,
    by_user BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


async def init_db(max_retries: int = 5) -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool
    last: Exception | None = None
    for attempt in range(max_retries):
        try:
            _pool = await asyncpg.create_pool(
                settings.DATABASE_URL, min_size=1, max_size=10, command_timeout=60
            )
            async with _pool.acquire() as con:
                await con.execute(SCHEMA)
                await con.execute("""
                    ALTER TABLE group_settings
                    ADD COLUMN IF NOT EXISTS asl_self_register BOOLEAN NOT NULL DEFAULT FALSE;
                    ALTER TABLE group_settings
                    ADD COLUMN IF NOT EXISTS title_ttl_seconds INTEGER NOT NULL DEFAULT 0;
                    ALTER TABLE group_settings
                    ADD COLUMN IF NOT EXISTS auto_reply_enabled BOOLEAN NOT NULL DEFAULT TRUE;
                """)
            log.info("PostgreSQL connected")
            return _pool
        except Exception as e:
            last = e
            wait = min(2 ** attempt, 16)
            log.warning("DB connect attempt %s failed — retry in %ss", attempt + 1, wait)
            await asyncio.sleep(wait)
    raise RuntimeError("PostgreSQL unavailable") from last


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("pool not initialized")
    return _pool


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
