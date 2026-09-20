"""Backup: pg_dump if available, else logical SQL via asyncpg."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from config import settings

log = logging.getLogger("POSSIBLY.backup")


async def create_backup() -> str | None:
    outdir = Path("backup")
    outdir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # 1) try pg_dump custom format
    dump_path = outdir / f"possibly_{stamp}.dump"
    try:
        proc = await asyncio.create_subprocess_exec(
            "pg_dump", "--format=custom", "--no-owner", "--no-acl",
            "--file", str(dump_path), settings.DATABASE_URL,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=120)
        if proc.returncode == 0 and dump_path.exists() and dump_path.stat().st_size > 0:
            log.info("pg_dump ok: %s", dump_path.name)
            return str(dump_path)
        dump_path.unlink(missing_ok=True)
    except Exception as e:
        log.warning("pg_dump unavailable/failed: %s", e)

    # 2) logical SQL via asyncpg
    sql_path = outdir / f"possibly_{stamp}.sql"
    try:
        from database.repositories import dump_all_tables_sql
        sql = await dump_all_tables_sql()
        sql_path.write_text(sql, encoding="utf-8")
        if sql_path.stat().st_size > 0:
            log.info("logical SQL backup ok: %s", sql_path.name)
            return str(sql_path)
    except Exception as e:
        log.warning("logical backup failed: %s", e)
        sql_path.unlink(missing_ok=True)

    return None
