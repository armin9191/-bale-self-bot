# main.py
from __future__ import annotations

import asyncio
import logging
import sys

from bot.api import BaleBotAPI
from bot.handlers import handle_message
from core.database import init_db
from core.config import BOT_TOKEN
from worker.session_worker import start_all_sessions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def poll_loop(bot: BaleBotAPI) -> None:
    offset = None
    bot.delete_webhook()
    me = bot.get_me()
    if me.get("ok"):
        u = me.get("result") or {}
        logger.info("Bot online: @%s (%s)", u.get("username"), u.get("id"))
        print(f"Bot ready: @{u.get('username')} id={u.get('id')}")
    else:
        logger.error("getMe failed: %s", me)
        print("توکن ربات نامعتبر است یا به API بله دسترسی نیست.")
        print(me)
        return

    print("Listening...")

    print(">>> calling start_all_sessions")
    try:
        await start_all_sessions()
        print(">>> start_all_sessions finished")
    except Exception as e:
        print(">>> start_all_sessions ERROR:", e)
        logger.exception("failed to start user sessions")

    while True:
        try:
            updates = await asyncio.to_thread(bot.get_updates, offset, 25)
            for upd in updates:
                offset = upd["update_id"] + 1
                msg = upd.get("message")
                if not msg:
                    continue
                try:
                    await handle_message(bot, msg)
                except Exception:
                    logger.exception("handler error")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error("poll error: %s", e)
            await asyncio.sleep(3)


def main() -> None:
    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        print("BOT_TOKEN را در core/config.py تنظیم کنید.")
        sys.exit(1)

    init_db()
    bot = BaleBotAPI(BOT_TOKEN)
    try:
        asyncio.run(poll_loop(bot))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()