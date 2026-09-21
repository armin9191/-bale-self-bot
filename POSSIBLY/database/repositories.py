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
