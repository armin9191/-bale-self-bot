# test_session.py
import asyncio
from pathlib import Path

from aiobale import Client, Dispatcher


async def main():
    p = Path("sessions/user_595450272.bale")
    print("exists:", p.exists())
    if p.exists():
        print("size:", p.stat().st_size)

    dp = Dispatcher()

    @dp.message()
    async def h(m):
        print("MSG:", m.text)

    client = Client(dp, session_file=p)
    print("starting client...")
    try:
        await client.start()
    except Exception as e:
        print("START ERROR:", type(e).__name__, e)


if __name__ == "__main__":
    asyncio.run(main())