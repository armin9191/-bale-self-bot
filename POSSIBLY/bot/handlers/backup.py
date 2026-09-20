"""PostgreSQL backup for POSSIBLY (Owner only)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from config import settings

log = logging.getLogger("POSSIBLY.backup")


async def create_backup() -> str | None:
    """
    Try pg_dump first. If unavailable or fails, return None.
    Caller must send the file only to the authorized Owner ID.
    Temporary file should be deleted after send by caller if desired.
    """
    outdir = Path("backup")
    outdir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = outdir / f"possibly_{stamp}.dump"

    # Never log the full DATABASE_URL
    try:
        proc = await asyncio.create_subprocess_exec(
            "pg_dump",
            "--format=custom",
            "--no-owner",
            "--no-acl",
            "--file",
            str(path),
            settings.DATABASE_URL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, err = await asyncio.wait_for(proc.communicate(), timeout=120)
        if proc.returncode != 0 or not path.exists() or path.stat().st_size == 0:
            log.warning("pg_dump failed (code=%s)", proc.returncode)
            if path.exists():
                path.unlink(missing_ok=True)
            return None
        log.info("Backup created: %s (%s bytes)", path.name, path.stat().st_size)
        return str(path)
    except FileNotFoundError:
        log.warning("pg_dump binary not found in environment")
        return None
    except Exception as e:
        log.warning("backup error: %s", e)
        if path.exists():
            path.unlink(missing_ok=True)
        return None
