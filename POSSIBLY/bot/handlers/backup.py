import asyncio
from pathlib import Path
from datetime import datetime
from config import settings

async def create_backup():
    outdir=Path("backup"); outdir.mkdir(exist_ok=True)
    path=outdir/f"possibly_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.dump"
    proc=await asyncio.create_subprocess_exec("pg_dump","--format=custom","--file",str(path),settings.DATABASE_URL,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
    _,err=await proc.communicate()
    if proc.returncode!=0 or not path.exists(): return None
    return str(path)
