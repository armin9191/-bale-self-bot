"""Repository layer."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from database.postgres import get_pool


async def upsert_user(user_id: int, username: Optional[str], display_name: str) -> None:
    await get_pool().execute(
        """INSERT INTO users(user_id,username,display_name) VALUES($1,$2,$3)
        ON CONFLICT(user_id) DO UPDATE SET username=EXCLUDED.username,
        display_name=EXCLUDED.display_name, last_seen=NOW()""",
        user_id, username, display_name or str(user_id),
    )


async def upsert_member(group_id: int, user_id: int, role: str = "member") -> None:
    await get_pool().execute(
        """INSERT INTO group_members(group_id,user_id,role) VALUES($1,$2,$3)
        ON CONFLICT(group_id,user_id) DO UPDATE SET role=EXCLUDED.role""",
        group_id, user_id, role,
    )


async def increment_stat(group_id: int, user_id: int, stat: str, day: date) -> None:
    allowed = {"messages", "gifs", "voice", "photos", "videos", "other"}
    if stat not in allowed:
        raise ValueError(stat)
    await get_pool().execute(
        f"""INSERT INTO daily_stats(group_id,user_id,date,{stat}) VALUES($1,$2,$3,1)
        ON CONFLICT(group_id,user_id,date) DO UPDATE SET {stat}=daily_stats.{stat}+1""",
        group_id, user_id, day,
    )


async def get_today_totals(group_id: int, day: date) -> dict[str, int]:
    row = await get_pool().fetchrow(
        """SELECT COALESCE(SUM(messages),0) messages, COALESCE(SUM(gifs),0) gifs,
        COALESCE(SUM(voice),0) voice, COALESCE(SUM(photos),0) photos,
        COALESCE(SUM(videos),0) videos, COALESCE(SUM(other),0) other
        FROM daily_stats WHERE group_id=$1 AND date=$2""",
        group_id, day,
    )
    return dict(row) if row else {}


async def get_top_users(group_id: int, day: date, limit: int = 5) -> list[dict]:
    rows = await get_pool().fetch(
        """SELECT u.username,u.display_name,ds.messages,ds.user_id
        FROM daily_stats ds LEFT JOIN users u ON u.user_id=ds.user_id
        WHERE ds.group_id=$1 AND ds.date=$2 ORDER BY ds.messages DESC LIMIT $3""",
        group_id, day, limit,
    )
    return [dict(r) for r in rows]


async def get_user_stats(user_id: int, group_id: int, day: date) -> dict:
    row = await get_pool().fetchrow(
        """SELECT * FROM daily_stats WHERE user_id=$1 AND group_id=$2 AND date=$3""",
        user_id, group_id, day,
    )
    return dict(row) if row else {"messages": 0, "gifs": 0, "voice": 0, "photos": 0, "videos": 0}


async def count_learned(group_id: int) -> int:
    return await get_pool().fetchval(
        "SELECT COUNT(*) FROM learned_words WHERE group_id=$1", group_id
    ) or 0


async def set_learned(group_id: int, trigger: str, response: str, created_by: int) -> None:
    await get_pool().execute(
        """INSERT INTO learned_words(group_id,trigger,response,created_by)
        VALUES($1,$2,$3,$4)
        ON CONFLICT(group_id,trigger) DO UPDATE SET response=EXCLUDED.response,
        created_by=EXCLUDED.created_by, created_at=NOW()""",
        group_id, trigger, response, created_by,
    )


async def delete_learned(group_id: int, trigger: str) -> bool:
    r = await get_pool().execute(
        "DELETE FROM learned_words WHERE group_id=$1 AND trigger=$2", group_id, trigger
    )
    return r.endswith("1")


async def list_learned_triggers(group_id: int) -> list[str]:
    rows = await get_pool().fetch(
        "SELECT trigger FROM learned_words WHERE group_id=$1 ORDER BY id", group_id
    )
    return [r["trigger"] for r in rows]


async def get_learned_response(group_id: int, trigger: str) -> Optional[str]:
    return await get_pool().fetchval(
        "SELECT response FROM learned_words WHERE group_id=$1 AND trigger=$2",
        group_id, trigger,
    )


async def log_moderation(group_id: int, actor_id: int, target_id: Optional[int], action: str, details: Optional[dict] = None) -> None:
    await get_pool().execute(
        """INSERT INTO moderation_logs(group_id,actor_id,target_id,action,details)
        VALUES($1,$2,$3,$4,$5::jsonb)""",
        group_id, actor_id, target_id, action, json.dumps(details or {}),
    )


async def recent_logs(group_id: int, limit: int = 15) -> list[dict]:
    rows = await get_pool().fetch(
        """SELECT * FROM moderation_logs WHERE group_id=$1 ORDER BY id DESC LIMIT $2""",
        group_id, limit,
    )
    return [dict(r) for r in rows]


async def create_whisper(group_id: int, sender_id: int, receiver_id: int, content: str, ttl: int) -> int:
    exp = datetime.now(timezone.utc) + timedelta(seconds=ttl)
    return await get_pool().fetchval(
        """INSERT INTO whispers(group_id,sender_id,receiver_id,encrypted_or_private_content,expires_at)
        VALUES($1,$2,$3,$4,$5) RETURNING id""",
        group_id, sender_id, receiver_id, content, exp,
    )


async def get_whisper(wid: int) -> Optional[dict]:
    row = await get_pool().fetchrow("SELECT * FROM whispers WHERE id=$1", wid)
    return dict(row) if row else None


async def mark_whisper_viewed(wid: int) -> None:
    await get_pool().execute("UPDATE whispers SET viewed=TRUE WHERE id=$1", wid)


async def list_group_members_seen(group_id: int, limit: int = 50) -> list[dict]:
    rows = await get_pool().fetch(
        """SELECT gm.user_id,gm.role,u.username,u.display_name
        FROM group_members gm LEFT JOIN users u ON u.user_id=gm.user_id
        WHERE gm.group_id=$1 ORDER BY gm.joined_at DESC LIMIT $2""",
        group_id, limit,
    )
    return [dict(r) for r in rows]


async def save_game(game_id: UUID, group_id: int, gtype: str, creator_id: int, status: str, state: dict) -> None:
    await get_pool().execute(
        """INSERT INTO games(game_id,group_id,type,creator_id,status,state)
        VALUES($1,$2,$3,$4,$5,$6::jsonb)
        ON CONFLICT(game_id) DO UPDATE SET status=EXCLUDED.status, state=EXCLUDED.state, updated_at=NOW()""",
        game_id, group_id, gtype, creator_id, status, json.dumps(state),
    )


async def load_active_game(group_id: int, gtype: str) -> Optional[dict]:
    row = await get_pool().fetchrow(
        """SELECT * FROM games WHERE group_id=$1 AND type=$2 AND status NOT IN ('ended','cancelled')
        ORDER BY created_at DESC LIMIT 1""",
        group_id, gtype,
    )
    return dict(row) if row else None


async def dump_all_tables_sql() -> str:
    """Logical SQL dump via asyncpg (works without pg_dump binary)."""
    pool = get_pool()
    tables = [
        "users", "group_members", "learned_words", "daily_stats",
        "games", "game_players", "whispers", "moderation_logs",
    ]
    lines = ["-- POSSIBLY logical SQL backup", f"-- {datetime.now(timezone.utc).isoformat()}", ""]
    async with pool.acquire() as con:
        for table in tables:
            lines.append(f"-- TABLE {table}")
            rows = await con.fetch(f"SELECT * FROM {table}")
            if not rows:
                lines.append(f"-- (empty) {table}")
                lines.append("")
                continue
            cols = list(rows[0].keys())
            col_list = ", ".join(cols)
            for r in rows:
                vals = []
                for c in cols:
                    v = r[c]
                    if v is None:
                        vals.append("NULL")
                    elif isinstance(v, (int, float)):
                        vals.append(str(v))
                    elif isinstance(v, bool):
                        vals.append("TRUE" if v else "FALSE")
                    elif isinstance(v, (dict, list)):
                        vals.append("'" + json.dumps(v, ensure_ascii=False).replace("'", "''") + "'::jsonb")
                    else:
                        s = str(v).replace("'", "''")
                        vals.append(f"'{s}'")
                lines.append(f"INSERT INTO {table} ({col_list}) VALUES ({', '.join(vals)});")
            lines.append("")
    return "\n".join(lines)


async def get_group_settings(group_id: int) -> dict:
    row = await get_pool().fetchrow(
        "SELECT rules_text, welcome_text, farewell_text FROM group_settings WHERE group_id=$1",
        group_id,
    )
    if not row:
        return {"rules_text": None, "welcome_text": None, "farewell_text": None}
    return dict(row)


async def set_group_rules(group_id: int, rules: str, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO group_settings(group_id, rules_text, updated_by, updated_at)
        VALUES($1,$2,$3,NOW())
        ON CONFLICT(group_id) DO UPDATE
        SET rules_text=EXCLUDED.rules_text, updated_by=EXCLUDED.updated_by, updated_at=NOW()""",
        group_id, rules, by,
    )


async def set_group_welcome(group_id: int, welcome: str, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO group_settings(group_id, welcome_text, updated_by, updated_at)
        VALUES($1,$2,$3,NOW())
        ON CONFLICT(group_id) DO UPDATE
        SET welcome_text=EXCLUDED.welcome_text, updated_by=EXCLUDED.updated_by, updated_at=NOW()""",
        group_id, welcome, by,
    )


async def set_group_farewell(group_id: int, farewell: str, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO group_settings(group_id, farewell_text, updated_by, updated_at)
        VALUES($1,$2,$3,NOW())
        ON CONFLICT(group_id) DO UPDATE
        SET farewell_text=EXCLUDED.farewell_text, updated_by=EXCLUDED.updated_by, updated_at=NOW()""",
        group_id, farewell, by,
    )


async def get_group_locks(group_id: int) -> dict[str, bool]:
    rows = await get_pool().fetch(
        "SELECT lock_key, enabled FROM group_locks WHERE group_id=$1",
        group_id,
    )
    return {r["lock_key"]: bool(r["enabled"]) for r in rows}


async def set_group_lock(group_id: int, lock_key: str, enabled: bool, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO group_locks(group_id, lock_key, enabled, updated_by, updated_at)
        VALUES($1,$2,$3,$4,NOW())
        ON CONFLICT(group_id, lock_key) DO UPDATE
        SET enabled=EXCLUDED.enabled, updated_by=EXCLUDED.updated_by, updated_at=NOW()""",
        group_id, lock_key, enabled, by,
    )


# ---------- special users ----------
async def add_special(group_id: int, user_id: int, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO special_users(group_id, user_id, granted_by)
        VALUES($1,$2,$3) ON CONFLICT DO NOTHING""",
        group_id, user_id, by,
    )


async def remove_special(group_id: int, user_id: int) -> bool:
    r = await get_pool().execute(
        "DELETE FROM special_users WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )
    return r.endswith("1")


async def clear_special(group_id: int) -> int:
    r = await get_pool().execute("DELETE FROM special_users WHERE group_id=$1", group_id)
    try:
        return int(r.split()[-1])
    except Exception:
        return 0


async def list_special(group_id: int) -> list[int]:
    rows = await get_pool().fetch(
        "SELECT user_id FROM special_users WHERE group_id=$1 ORDER BY created_at",
        group_id,
    )
    return [int(r["user_id"]) for r in rows]


async def is_special_user(group_id: int, user_id: int) -> bool:
    row = await get_pool().fetchval(
        "SELECT 1 FROM special_users WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )
    return row is not None


# ---------- titles (لقب) ----------
async def set_title(group_id: int, user_id: int, title: str, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO user_titles(group_id, user_id, title, set_by)
        VALUES($1,$2,$3,$4)
        ON CONFLICT(group_id, user_id) DO UPDATE
        SET title=EXCLUDED.title, set_by=EXCLUDED.set_by, created_at=NOW()""",
        group_id, user_id, title, by,
    )


async def get_title(group_id: int, user_id: int) -> str | None:
    return await get_pool().fetchval(
        "SELECT title FROM user_titles WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )


async def delete_title(group_id: int, user_id: int) -> bool:
    r = await get_pool().execute(
        "DELETE FROM user_titles WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )
    return r.endswith("1")


async def list_titles(group_id: int) -> list[dict]:
    rows = await get_pool().fetch(
        "SELECT user_id, title FROM user_titles WHERE group_id=$1 ORDER BY created_at DESC",
        group_id,
    )
    return [dict(r) for r in rows]


async def set_title_ttl(group_id: int, seconds: int, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO group_settings(group_id, title_ttl_seconds, updated_by, updated_at)
        VALUES($1,$2,$3,NOW())
        ON CONFLICT(group_id) DO UPDATE
        SET title_ttl_seconds=EXCLUDED.title_ttl_seconds, updated_by=EXCLUDED.updated_by, updated_at=NOW()""",
        group_id, seconds, by,
    )


async def get_title_ttl(group_id: int) -> int:
    v = await get_pool().fetchval(
        "SELECT title_ttl_seconds FROM group_settings WHERE group_id=$1", group_id
    )
    return int(v or 0)


# ---------- ASL / اصل ----------
async def set_asl(group_id: int, user_id: int, body: str, by: int) -> None:
    pool = get_pool()
    old = await pool.fetchval(
        "SELECT body FROM asl_profiles WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )
    if old and old != body:
        await pool.execute(
            "INSERT INTO asl_history(group_id, user_id, body) VALUES($1,$2,$3)",
            group_id, user_id, old,
        )
    await pool.execute(
        """INSERT INTO asl_profiles(group_id, user_id, body, updated_by, updated_at)
        VALUES($1,$2,$3,$4,NOW())
        ON CONFLICT(group_id, user_id) DO UPDATE
        SET body=EXCLUDED.body, updated_by=EXCLUDED.updated_by, updated_at=NOW()""",
        group_id, user_id, body, by,
    )


async def get_asl(group_id: int, user_id: int) -> dict | None:
    row = await get_pool().fetchrow(
        "SELECT * FROM asl_profiles WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )
    return dict(row) if row else None


async def delete_asl(group_id: int, user_id: int) -> bool:
    r = await get_pool().execute(
        "DELETE FROM asl_profiles WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )
    await get_pool().execute(
        "DELETE FROM asl_likes WHERE group_id=$1 AND target_id=$2",
        group_id, user_id,
    )
    return r.endswith("1")


async def set_asl_verified(group_id: int, user_id: int, verified: bool) -> None:
    await get_pool().execute(
        """UPDATE asl_profiles SET verified=$3 WHERE group_id=$1 AND user_id=$2""",
        group_id, user_id, verified,
    )


async def set_asl_self_register(group_id: int, enabled: bool, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO group_settings(group_id, asl_self_register, updated_by, updated_at)
        VALUES($1,$2,$3,NOW())
        ON CONFLICT(group_id) DO UPDATE
        SET asl_self_register=EXCLUDED.asl_self_register, updated_by=EXCLUDED.updated_by, updated_at=NOW()""",
        group_id, enabled, by,
    )


async def get_asl_self_register(group_id: int) -> bool:
    v = await get_pool().fetchval(
        "SELECT asl_self_register FROM group_settings WHERE group_id=$1", group_id
    )
    return bool(v)


async def list_asl(group_id: int, limit: int = 50) -> list[dict]:
    rows = await get_pool().fetch(
        """SELECT user_id, body, verified, likes, views FROM asl_profiles
        WHERE group_id=$1 ORDER BY likes DESC, updated_at DESC LIMIT $2""",
        group_id, limit,
    )
    return [dict(r) for r in rows]


async def random_asl(group_id: int) -> dict | None:
    row = await get_pool().fetchrow(
        """SELECT * FROM asl_profiles WHERE group_id=$1 ORDER BY random() LIMIT 1""",
        group_id,
    )
    return dict(row) if row else None


async def top_asl(group_id: int, n: int = 5) -> list[dict]:
    rows = await get_pool().fetch(
        """SELECT user_id, body, likes, views, verified FROM asl_profiles
        WHERE group_id=$1 ORDER BY likes DESC LIMIT $2""",
        group_id, n,
    )
    return [dict(r) for r in rows]


async def search_asl(group_id: int, q: str, limit: int = 20) -> list[dict]:
    rows = await get_pool().fetch(
        """SELECT user_id, body, likes, verified FROM asl_profiles
        WHERE group_id=$1 AND body ILIKE $2 ORDER BY likes DESC LIMIT $3""",
        group_id, f"%{q}%", limit,
    )
    return [dict(r) for r in rows]


async def asl_stats(group_id: int) -> dict:
    row = await get_pool().fetchrow(
        """SELECT COUNT(*)::int AS total,
                  COALESCE(SUM(likes),0)::int AS likes,
                  COALESCE(SUM(views),0)::int AS views,
                  COUNT(*) FILTER (WHERE verified)::int AS verified
           FROM asl_profiles WHERE group_id=$1""",
        group_id,
    )
    return dict(row) if row else {"total": 0, "likes": 0, "views": 0, "verified": 0}


async def asl_history(group_id: int, user_id: int, limit: int = 10) -> list[dict]:
    rows = await get_pool().fetch(
        """SELECT body, created_at FROM asl_history
        WHERE group_id=$1 AND user_id=$2 ORDER BY created_at DESC LIMIT $3""",
        group_id, user_id, limit,
    )
    return [dict(r) for r in rows]


async def inc_asl_view(group_id: int, user_id: int) -> None:
    await get_pool().execute(
        "UPDATE asl_profiles SET views=views+1 WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )


async def toggle_asl_like(group_id: int, target_id: int, liker_id: int) -> tuple[bool, int]:
    """Returns (liked_now, total_likes)."""
    pool = get_pool()
    exists = await pool.fetchval(
        "SELECT 1 FROM asl_likes WHERE group_id=$1 AND target_id=$2 AND liker_id=$3",
        group_id, target_id, liker_id,
    )
    if exists:
        await pool.execute(
            "DELETE FROM asl_likes WHERE group_id=$1 AND target_id=$2 AND liker_id=$3",
            group_id, target_id, liker_id,
        )
        await pool.execute(
            "UPDATE asl_profiles SET likes=GREATEST(likes-1,0) WHERE group_id=$1 AND user_id=$2",
            group_id, target_id,
        )
        liked = False
    else:
        await pool.execute(
            "INSERT INTO asl_likes(group_id, target_id, liker_id) VALUES($1,$2,$3) ON CONFLICT DO NOTHING",
            group_id, target_id, liker_id,
        )
        await pool.execute(
            "UPDATE asl_profiles SET likes=likes+1 WHERE group_id=$1 AND user_id=$2",
            group_id, target_id,
        )
        liked = True
    total = await pool.fetchval(
        "SELECT likes FROM asl_profiles WHERE group_id=$1 AND user_id=$2",
        group_id, target_id,
    )
    return liked, int(total or 0)


# ---------- mute / warn / protect / personal locks / managers ----------
async def get_warnings(group_id: int, user_id: int) -> int:
    v = await get_pool().fetchval(
        "SELECT count FROM user_warnings WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )
    return int(v or 0)


async def clear_warnings(group_id: int, user_id: int) -> None:
    await get_pool().execute(
        "DELETE FROM user_warnings WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )


async def add_warning(group_id: int, user_id: int) -> int:
    await get_pool().execute(
        """INSERT INTO user_warnings(group_id, user_id, count) VALUES($1,$2,1)
        ON CONFLICT(group_id, user_id) DO UPDATE SET count=user_warnings.count+1""",
        group_id, user_id,
    )
    return await get_warnings(group_id, user_id)


async def set_mute(group_id: int, user_id: int, until_ts, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO user_mutes(group_id, user_id, until_ts, muted_by)
        VALUES($1,$2,$3,$4)
        ON CONFLICT(group_id, user_id) DO UPDATE
        SET until_ts=EXCLUDED.until_ts, muted_by=EXCLUDED.muted_by""",
        group_id, user_id, until_ts, by,
    )


async def clear_mute(group_id: int, user_id: int) -> None:
    await get_pool().execute(
        "DELETE FROM user_mutes WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )


async def get_mute(group_id: int, user_id: int):
    return await get_pool().fetchrow(
        "SELECT until_ts, muted_by FROM user_mutes WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )


async def set_protection(group_id: int, user_id: int, protected: bool, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO user_protection(group_id, user_id, protected, set_by)
        VALUES($1,$2,$3,$4)
        ON CONFLICT(group_id, user_id) DO UPDATE
        SET protected=EXCLUDED.protected, set_by=EXCLUDED.set_by""",
        group_id, user_id, protected, by,
    )


async def is_protected(group_id: int, user_id: int) -> bool:
    v = await get_pool().fetchval(
        "SELECT protected FROM user_protection WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )
    return bool(v)


async def set_personal_lock(group_id: int, user_id: int, lock_key: str, mode: str) -> None:
    await get_pool().execute(
        """INSERT INTO user_personal_locks(group_id, user_id, lock_key, mode)
        VALUES($1,$2,$3,$4)
        ON CONFLICT(group_id, user_id, lock_key) DO UPDATE SET mode=EXCLUDED.mode""",
        group_id, user_id, lock_key, mode,
    )


async def get_personal_locks(group_id: int, user_id: int) -> dict[str, str]:
    rows = await get_pool().fetch(
        "SELECT lock_key, mode FROM user_personal_locks WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )
    return {r["lock_key"]: r["mode"] for r in rows}


async def clear_personal_locks(group_id: int, user_id: int) -> None:
    await get_pool().execute(
        "DELETE FROM user_personal_locks WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )


async def add_bot_manager(group_id: int, user_id: int, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO bot_managers(group_id, user_id, granted_by)
        VALUES($1,$2,$3) ON CONFLICT DO NOTHING""",
        group_id, user_id, by,
    )


async def remove_bot_manager(group_id: int, user_id: int) -> None:
    await get_pool().execute(
        "DELETE FROM bot_managers WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )


async def is_bot_manager(group_id: int, user_id: int) -> bool:
    v = await get_pool().fetchval(
        "SELECT 1 FROM bot_managers WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )
    return v is not None


# ---------- force join ----------
async def set_force_join(group_id: int, channel_id: str, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO force_join(group_id, channel_id, set_by, updated_at)
        VALUES($1,$2,$3,NOW())
        ON CONFLICT(group_id) DO UPDATE
        SET channel_id=EXCLUDED.channel_id, set_by=EXCLUDED.set_by, updated_at=NOW()""",
        group_id, channel_id, by,
    )


async def clear_force_join(group_id: int) -> None:
    await get_pool().execute("DELETE FROM force_join WHERE group_id=$1", group_id)


async def get_force_join(group_id: int) -> str | None:
    return await get_pool().fetchval(
        "SELECT channel_id FROM force_join WHERE group_id=$1", group_id
    )


# ---------- group lock ----------
async def get_group_lock(group_id: int) -> dict:
    row = await get_pool().fetchrow(
        "SELECT locked, until_ts, daily_start, daily_end FROM group_lock_state WHERE group_id=$1",
        group_id,
    )
    if not row:
        return {"locked": False, "until_ts": None, "daily_start": None, "daily_end": None}
    return dict(row)


async def set_group_lock_manual(group_id: int, locked: bool, by: int, until_ts=None) -> None:
    await get_pool().execute(
        """INSERT INTO group_lock_state(group_id, locked, until_ts, set_by, updated_at)
        VALUES($1,$2,$3,$4,NOW())
        ON CONFLICT(group_id) DO UPDATE
        SET locked=EXCLUDED.locked, until_ts=EXCLUDED.until_ts, set_by=EXCLUDED.set_by, updated_at=NOW()""",
        group_id, locked, until_ts, by,
    )


async def set_group_lock_daily(group_id: int, start: str, end: str, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO group_lock_state(group_id, locked, daily_start, daily_end, set_by, updated_at)
        VALUES($1,FALSE,$2,$3,$4,NOW())
        ON CONFLICT(group_id) DO UPDATE
        SET daily_start=EXCLUDED.daily_start, daily_end=EXCLUDED.daily_end,
            set_by=EXCLUDED.set_by, updated_at=NOW()""",
        group_id, start, end, by,
    )


async def clear_group_lock_daily(group_id: int) -> None:
    await get_pool().execute(
        "UPDATE group_lock_state SET daily_start=NULL, daily_end=NULL WHERE group_id=$1",
        group_id,
    )


# ---------- mute records (richer) ----------
async def set_mute_full(group_id: int, user_id: int, until_ts, by: int, reason: str | None = None) -> None:
    await get_pool().execute(
        """INSERT INTO mute_records(group_id, user_id, until_ts, reason, muted_by, created_at)
        VALUES($1,$2,$3,$4,$5,NOW())
        ON CONFLICT(group_id, user_id) DO UPDATE
        SET until_ts=EXCLUDED.until_ts, reason=COALESCE(EXCLUDED.reason, mute_records.reason),
            muted_by=EXCLUDED.muted_by, created_at=NOW()""",
        group_id, user_id, until_ts, reason, by,
    )
    # keep legacy table in sync
    await set_mute(group_id, user_id, until_ts, by)


async def clear_mute_full(group_id: int, user_id: int) -> None:
    await get_pool().execute(
        "DELETE FROM mute_records WHERE group_id=$1 AND user_id=$2", group_id, user_id
    )
    await clear_mute(group_id, user_id)


async def list_mutes(group_id: int) -> list[dict]:
    rows = await get_pool().fetch(
        "SELECT user_id, until_ts, reason, muted_by FROM mute_records WHERE group_id=$1 ORDER BY created_at DESC",
        group_id,
    )
    return [dict(r) for r in rows]


async def clear_all_mutes(group_id: int) -> int:
    r = await get_pool().execute("DELETE FROM mute_records WHERE group_id=$1", group_id)
    await get_pool().execute("DELETE FROM user_mutes WHERE group_id=$1", group_id)
    try:
        return int(r.split()[-1])
    except Exception:
        return 0


async def get_mute_full(group_id: int, user_id: int):
    row = await get_pool().fetchrow(
        "SELECT until_ts, reason, muted_by FROM mute_records WHERE group_id=$1 AND user_id=$2",
        group_id, user_id,
    )
    if row:
        return dict(row)
    row2 = await get_mute(group_id, user_id)
    return dict(row2) if row2 else None


# ---------- warnings rich ----------
async def set_max_warns(group_id: int, n: int, by: int) -> None:
    await get_pool().execute(
        """INSERT INTO warn_settings(group_id, max_warns, updated_by)
        VALUES($1,$2,$3)
        ON CONFLICT(group_id) DO UPDATE SET max_warns=EXCLUDED.max_warns, updated_by=EXCLUDED.updated_by""",
        group_id, n, by,
    )


async def get_max_warns(group_id: int) -> int:
    v = await get_pool().fetchval("SELECT max_warns FROM warn_settings WHERE group_id=$1", group_id)
    return int(v or 3)


async def add_warn_record(group_id: int, user_id: int, by: int, reason: str | None = None) -> int:
    await get_pool().execute(
        "INSERT INTO warn_records(group_id, user_id, reason, by_user) VALUES($1,$2,$3,$4)",
        group_id, user_id, reason, by,
    )
    return await add_warning(group_id, user_id)


async def remove_one_warn(group_id: int, user_id: int) -> int:
    c = await get_warnings(group_id, user_id)
    if c <= 0:
        return 0
    new_c = c - 1
    if new_c <= 0:
        await clear_warnings(group_id, user_id)
        return 0
    await get_pool().execute(
        "UPDATE user_warnings SET count=$3 WHERE group_id=$1 AND user_id=$2",
        group_id, user_id, new_c,
    )
    return new_c


async def list_warns(group_id: int) -> list[dict]:
    rows = await get_pool().fetch(
        "SELECT user_id, count FROM user_warnings WHERE group_id=$1 AND count>0 ORDER BY count DESC",
        group_id,
    )
    return [dict(r) for r in rows]


async def clear_all_warns(group_id: int) -> int:
    r = await get_pool().execute("DELETE FROM user_warnings WHERE group_id=$1", group_id)
    try:
        return int(r.split()[-1])
    except Exception:
        return 0
