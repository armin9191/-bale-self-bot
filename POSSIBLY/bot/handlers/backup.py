"""Backup: prefer logical SQL (for Owner PM), fallback pg_dump."""
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

    # 1) Logical SQL via asyncpg (always preferred for easy restore & user request)
    sql_path = outdir / f"possibly_{stamp}.sql"
    try:
        from database.repositories import dump_all_tables_sql
        sql = await dump_all_tables_sql()
        sql_path.write_text(sql, encoding="utf-8")
        if sql_path.stat().st_size > 0:
            log.info("logical SQL backup ok: %s (%s bytes)", sql_path.name, sql_path.stat().st_size)
            return str(sql_path)
    except Exception as e:
        log.warning("logical backup failed: %s", e)
        sql_path.unlink(missing_ok=True)

    # 2) pg_dump custom format if SQL failed
    dump_path = outdir / f"possibly_{stamp}.dump"
    try:
        proc = await asyncio.create_subprocess_exec(
            "pg_dump", "--format=plain", "--no-owner", "--no-acl",
            "--file", str(dump_path), settings.DATABASE_URL,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=120)
        if proc.returncode == 0 and dump_path.exists() and dump_path.stat().st_size > 0:
            # rename to .sql for consistency
            final = outdir / f"possibly_{stamp}_pg.sql"
            dump_path.rename(final)
            log.info("pg_dump ok: %s", final.name)
            return str(final)
        dump_path.unlink(missing_ok=True)
    except Exception as e:
        log.warning("pg_dump unavailable/failed: %s", e)

    return None
